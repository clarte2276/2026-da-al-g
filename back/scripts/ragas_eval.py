"""Evaluate the local Graph RAG with RAGAS and the configured OpenAI key.

Run from ``back`` with ``uv run --extra eval python -m scripts.ragas_eval``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, Literal

from openai import AsyncOpenAI
from ragas.embeddings.base import embedding_factory
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerCorrectness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)
from ragas.metrics.collections.answer_relevancy.util import (
    AnswerRelevanceInput,
    AnswerRelevanceOutput,
    AnswerRelevancePrompt,
)
from ragas.metrics.collections.context_recall.util import (
    ContextRecallClassification,
    ContextRecallInput,
    ContextRecallOutput,
    ContextRecallPrompt,
)
from ragas.metrics.collections.faithfulness.util import (
    NLIStatementInput,
    NLIStatementOutput,
    NLIStatementPrompt,
    StatementFaithfulnessAnswer,
    StatementGeneratorInput,
    StatementGeneratorOutput,
    StatementGeneratorPrompt,
)
from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.main import chat_service, rag_service
from app.models import DocumentContent, DocumentLink

RULE_VERSION = "35315ef6-c82f-44fd-904c-62b78bdc474a"
DATASET_VERSION = "2026.09.16-v2"


@dataclass(frozen=True, slots=True)
class DocumentCase:
    name: str
    question: str
    reference_articles: tuple[int, ...]
    graph_required: bool = False


@dataclass(frozen=True, slots=True)
class GeneralCase:
    name: str
    question: str
    reference: str


DOCUMENT_CASES = [
    DocumentCase(
        "vehicle_failure",
        "열차 운전 중 차량고장으로 자력운전이 곤란하면 어떤 조치를 해야 하나요?",
        (326,),
    ),
    DocumentCase(
        "brake_pipe",
        "정거장 외에서 제동관 또는 공기관 고장으로 통기불능이면 구원과 운전을 어떻게 처리하나요?",
        (327,),
    ),
    DocumentCase(
        "door_failure",
        "열차 운전 중 출입문 고장이 발생하면 보고, 방송, 응급조치와 회송은 어떻게 하나요?",
        (328,),
    ),
    DocumentCase(
        "rescue_train_protection",
        "정거장 외에서 사고로 정차한 열차가 구원열차를 요구했을 때 열차방호는 어떻게 하나요?",
        (321,),
    ),
    DocumentCase(
        "adjacent_line_protection",
        "정거장 외에서 인접 선로를 지장한 경우 어떤 방호와 보고를 해야 하나요?",
        (323,),
    ),
    DocumentCase(
        "automatic_driving",
        "5~8호선 본선 구간의 운전 방식은 자동운전인가요? 수동운전 예외는 무엇인가요?",
        (330,),
    ),
    DocumentCase(
        "front_cab_failure",
        "전동차 전부 운전실이 고장 나면 어떤 속도로 어디까지 운전할 수 있나요?",
        (331,),
    ),
    DocumentCase(
        "runaway_vehicle",
        "유치 중인 차량이 자동으로 굴렀을 때 누구에게 보고하고 어떻게 정차시키나요?",
        (332,),
    ),
    DocumentCase(
        "storm",
        "열차 운전 중 폭풍을 만나 운전에 위험하다고 판단되면 기관사는 어떻게 해야 하나요?",
        (348,),
    ),
    DocumentCase(
        "flooding",
        "터널 내 침수로 정전이나 운전 지장이 우려될 때 승무원과 역은 어떻게 조치하나요?",
        (349,),
    ),
    DocumentCase(
        "fog_or_snowstorm",
        "안개나 눈보라로 신호 확인이 어려울 때 기관사와 운전관제는 어떻게 조치하나요?",
        (351, 352),
    ),
    DocumentCase(
        "weather_alert",
        "이상기후 경보의 종류와 열차 운전 규제는 어떻게 정하나요?",
        (345, 346),
    ),
    DocumentCase(
        "guide_door",
        "6호선 전동차 출입문 전체 열림불능 시 점검사항과 조치는 무엇인가요?",
        (328,),
        graph_required=True,
    ),
    DocumentCase(
        "guide_psd",
        "승강장안전문 PSD 무선 닫힘불능으로 수동닫힘을 여러 역에서 취급할 때 조치는 무엇인가요?",
        (46, 242),
        graph_required=True,
    ),
    DocumentCase(
        "guide_pantograph",
        "6호선 전동차 판토그래프 상승불능 시 점검과 운전관제 보고는 어떻게 하나요?",
        (35, 74),
        graph_required=True,
    ),
    DocumentCase(
        "guide_emergency_brake",
        "6호선 전동차 비상제동 풀림불능 시 점검과 조치는 무엇인가요?",
        (25,),
        graph_required=True,
    ),
    DocumentCase(
        "guide_atc",
        "6호선 전동차 ATC 장치 고장 시 운전과 회송 조치는 어떻게 하나요?",
        (34, 144),
        graph_required=True,
    ),
]

GENERAL_CASES = [
    GeneralCase("greeting", "안녕", "안녕하세요! 무엇을 도와드릴까요?"),
    GeneralCase("capital", "대한민국의 수도는 어디야?", "대한민국의 수도는 서울특별시입니다."),
    GeneralCase("boiling_point", "표준 대기압에서 물은 몇 도에 끓어?", "표준 대기압(1기압)에서 물의 끓는점은 섭씨 100도(100℃)입니다."),
    GeneralCase("addition", "2 더하기 2는 얼마야?", "2 더하기 2는 4입니다."),
    GeneralCase(
        "rag_definition",
        "RAG가 무엇인지 일반적인 개념으로 설명해줘.",
        "RAG(Retrieval-Augmented Generation, 검색 증강 생성)는 대규모 언어 모델이 답변을 생성할 때 외부 지식 베이스나 문서에서 관련된 정보를 먼저 검색(Retrieval)한 후, 이를 바탕으로 정확하고 신뢰성 높은 답변을 생성(Generation)하는 인공지능 기술입니다.",
    ),
]

REFERENCE_V2: dict[str, dict[str, str]] = {
    "vehicle_failure": {
        "reference": (
            "열차 운전 중 차량고장 등으로 자력운전이 곤란하다고 인정될 때는 운전관제에게 보고하고 구원열차를 요구하여야 합니다. "
            "또한 무동력 또는 기타 사유로 구름의 우려가 있을 때에는 반드시 구름방지 조치를 시행하여야 합니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제326조(차량고장인 경우)",
        "rationale": "원문 규정 제326조에 따른 자력운전 곤란 시 관제 보고, 구원열차 요구, 구름방지 조치 명시",
    },
    "brake_pipe": {
        "reference": (
            "정거장 외에서 제동관 또는 공기관 고장으로 통기불능일 때는 구원을 요구하여야 합니다. "
            "다만 상황에 따라 안전하다고 인정될 때에는 최근정거장까지 주의운전할 수 있으며, "
            "여객열차인 경우 최근정거장까지 운전하고 잔여운전에 대하여 운전관제의 지시를 받아 열차를 교환수배하여야 합니다. "
            "운전 시에는 정차 시 수동제동기 또는 주차제동기를 걸고 출발 시 푸는 적당한 조치를 취하여야 합니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제327조(제동관 및 공기관 고장인 경우의 조치)",
        "rationale": "원문 규정 제327조에 명시된 구원요구, 여객열차 최근정거장 주의운전, 관제 지시 및 수동/주차제동기 취급 조건 반영",
    },
    "door_failure": {
        "reference": (
            "열차 운전 중 출입문 고장이 발생하면 운전관제에 보고하고 승객 대상 안내방송을 실시하며, "
            "출입문이 정상작동하기 위한 응급조치를 시행합니다. 출입문 1개 이상 고장 발생으로 정상작동 불가 시 "
            "운전관제에 보고하고 지시에 의하여 회송 조치하여야 합니다(단, 마지막열차는 출입문안전막 설치 조치 후 차량교환역까지 운행 가능)."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제328조(열차의 출입문 고장인 경우)",
        "rationale": "질문에서 요구한 보고, 방송, 응급조치, 회송 4단계 요건을 규정 제328조에 따라 완전하게 수록",
    },
    "rescue_train_protection": {
        "reference": (
            "정거장 외에서 열차사고 기타 등으로 정차한 열차가 구원열차를 요구하였거나 구원열차 운전 통보가 있었을 때에는 "
            "제2종 방호를 하여야 합니다. 다만 구원열차가 오지 않음이 확실한 방향은 방호를 생략할 수 있습니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제321조(구원열차에 대한 정차열차의 방호)",
        "rationale": "정거장 외 구원열차 요구 시 방호에 대한 규정 제321조 제2종 방호 원문 반영",
    },
    "adjacent_line_protection": {
        "reference": (
            "정거장 외에서 탈선·전복 등으로 인접 선로를 지장하였을 때에는 후속열차 방호를 하기 전에 그 인접선로를 운전하는 열차에 대하여 "
            "지장지점 전후 양방향에 제1종 방호를 시행하여야 합니다. 자동폐색식 또는 차내신호폐색식 구간인 경우 즉시 단락용 동선으로 궤도회로를 단락하여야 합니다. "
            "운전 중 인접선로 장애 발견 시 신속히 열차를 정차시키고 운전관제에게 보고 및 지장지역 전후 양방향에 제1종 방호를 시행하며, "
            "보고를 받은 운전관제는 접근 열차에 비상정차 조치를 취합니다. 열차가 진행해 오지 않는 방향에 대한 방호는 생략할 수 있습니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제323조(인접선로를 지장한 경우의 방호)",
        "rationale": "인접선로 지장 시 제1종 방호, 궤도회로 단락, 관제 보고 및 비상정차 조치 수록",
    },
    "automatic_driving": {
        "reference": (
            "5~8호선 본선 구간의 운전 방식은 자동운전을 원칙으로 합니다. "
            "다만 1) 서행 운전명령 구간 진입, 2) 정지신호로 승강장 중간 정차 후 정차위치 이동, 3) ATO 기능이상 등으로 운전관제의 수동운전 지시, "
            "4) 수동운전 적용시간 운영, 5) 회송열차 운전 등의 경우에는 수동운전에 의합니다. "
            "운전방식 변경을 위해 자동모드에서 다른 모드로 변경하고자 할 때에는 운전관제의 승인을 받아야 합니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제330조(5~8호선 구간에서의 운전방식)",
        "rationale": "5~8호선 자동운전 원칙과 5가지 수동운전 예외 규정을 완결성 있게 반영",
    },
    "front_cab_failure": {
        "reference": (
            "전동차 전부 운전실 고장으로 전부운전실에서 운전할 수 없을 때에는 후부운전실에서 25km/h 이하의 속도로 운전할 수 있으며, "
            "최근정거장까지만 운전하여야 합니다. 이때 차장 또는 1인승무열차의 기관사(지도요원 포함)는 최전부 운전실에 승차하여 전방 신호 및 진로를 확인하여야 합니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제331조(전동차의 전부 운전실이 고장인 경우의 조치)",
        "rationale": "질문에서 묻는 운전 속도(25km/h 이하), 운전 한도(최근정거장까지), 최전부 승차 요건 명시",
    },
    "runaway_vehicle": {
        "reference": (
            "유치 중인 차량이 자동으로 굴렀을 경우 역·소장은 즉시 상대역·소장 및 운전관제에게 그 요지를 급보하고 정차시킬 조치를 하여야 합니다. "
            "급보를 받은 운전관제, 역, 소장은 차량 정차에 노력하고 필요한 경우 인접 정거장 역·소장에게 통보하며 관계 선로 및 인접선로 운행 열차의 기관사에게 주의를 환기시킵니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제332조(차량이 자동으로 굴렀을 경우의 조치)",
        "rationale": "유치차량 자동 구름 시 상대역/소장/관제 급보와 정차 조치 규정 명시",
    },
    "storm": {
        "reference": (
            "열차 운전 중 폭풍을 만났을 때 기관사는 열차속도에 급격한 변화를 주지 않도록 하고, "
            "열차운전에 위험하다고 판단될 때에는 안전한 장소에 열차를 정차시켜야 합니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제348조(폭풍에 대한 기관사의 조치)",
        "rationale": "폭풍 시 급격한 속도 변화 방지 및 안전장소 정차 조치 규정 반영",
    },
    "flooding": {
        "reference": (
            "터널 내 침수로 정전이나 운전 지장 우려가 있을 때 승무원은 지체 없이 운전관제에 보고하고 지시를 받아야 합니다. "
            "역장 또는 소장은 운전관제의 명령에 의하여 승객을 정거장에 하차시킨 후 전동차를 침수되지 않을 장소로 회송하여야 하며, "
            "관제 지시를 받을 수 없을 때에는 정거장에 승객을 하차시킨 후 지체 없이 운전관제에게 보고합니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제349조(침수시의 열차 운전취급)",
        "rationale": "터널 침수 시 승무원의 관제 보고와 역장/소장의 승객 하차 및 전동차 회송 조치 수록",
    },
    "fog_or_snowstorm": {
        "reference": (
            "안개나 눈보라로 신호 확인이 어려울 때 기관사는 신호 확인거리 범위 내에서 정차할 수 있는 속도로 주의운전을 하여야 합니다. "
            "신호기 현시 확인 불능 시 일단 정차하고 출발신호기 확인 불능 시 관제/역장 구두통보에 의하여 진행하며, 관제에게 상황을 통보합니다. "
            "운전관제는 신호 확인거리가 50m 이하일 때 장내신호기에 주의 또는 경계신호를 현시하고 필요 시 열차 운전중지 명령을 내리며, "
            "기관사는 운전중지 명령이 없는 한 15km/h 이하의 속도로 운전하여야 합니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제351조, 제352조",
        "rationale": "기관사의 확인거리 내 주의운전·정차·보고와 관제의 50m 이하 경계 현시·운전중지 명령 및 15km/h 이하 운전 규정 통합 반영",
    },
    "weather_alert": {
        "reference": (
            "이상기후 경보의 종류는 주의를 요하는 예보, 열차운전에 지장이 예상되는 경보, 지장 또는 피해발생으로 계속 잔여운전이 위험한 비상경보로 구분 발령합니다. "
            "운전관제는 재해 발생 또는 예상 시 운전속도 감속지시, 열차운행 일시중지 또는 운행취소 등의 운전정리를 시행하며, 안전을 최우선으로 하여 운전을 규제합니다."
        ),
        "source_doc": "운전취급규정.hwp (35315ef6-c82f-44fd-904c-62b78bdc474a)",
        "source_location": "제345조(경보구분), 제346조(운전의 규제)",
        "rationale": "경보 3단계(예보, 경보, 비상경보)와 관제의 운전정리 규제 조치 명시",
    },
    "guide_door": {
        "reference": (
            "6호선 전동차 출입문 전체 열림불능 시 먼저 정위치 정차 미달·진과정차, Dwell Light 소등, ODL/ODR 미수신 여부를 확인합니다. "
            "진과정차 시에는 운전모드 비상, 역전기 후진, 출입문 수/수로 정위치 조정운전을 시행합니다. "
            "점검사항으로 전부Tc차 AP.CB1KPHL/R(1Km/h 계전기 전원) 차단 여부를 확인하여 차단 시 복귀하고, 1Km/h 계전기(CE.RL1KPHL/R)를 가볍게 두드려 보며, 전부Tc차 AP.CBDO4TC 차단 여부를 점검하여 차단 시 복귀합니다. "
            "조치사항으로 ATC 정상 시에는 운전모드 수동 및 출입문 수/수 전환 후 측면 출입문열림버튼을 취급하고, ATC 고장 시에는 운전모드 비상 및 출입문 수/수 전환 후 측면 버튼을 취급합니다. "
            "개방 불능 시 승객안내방송 후 운전관제에 보고하여 지시를 받으며, 후부Tc차에서 출입문 취급 후 회송 조치합니다(규정 제328조)."
        ),
        "source_doc": "6호선 응급조치 가이드-1.pptx (61b7c6ec-e756-49be-9702-9e4420e0f599) 슬라이드 48, 50 및 운전취급규정.hwp 제328조",
        "source_location": "가이드-1 Slide 48, 50 / 규정 제328조",
        "rationale": "기존 제328조 규정 외에 6호선 전동차의 1Km/h 계전기, NFB 차단기, 수동/비상 조치, 측면 열림버튼 등 실제 가이드 점검·조치 절차를 원문 기반으로 보강",
    },
    "guide_psd": {
        "reference": (
            "승강장안전문(PSD) 무선(RF) 닫힘불능 시 차상 PSD 무선(RF) 장치의 노선모드에서 운행 방향(상선 또는 하선)이 맞게 선택되었는지 확인 후 출입문 닫힘을 취급합니다. "
            "복귀되지 않을 경우 차상 PSD 무선 장치 우측면 전원 스위치를 RESET한 후 출입문 닫힘을 취급합니다. "
            "기관사조작반 수동닫힘을 2개역 이상 연속 취급할 때에는 운전관제에 상황을 보고하여 지시를 받고, "
            "규정 제46조 및 제242조에 따라 역장에게 열차감시 및 출발지시전호를 의뢰하며, 승강장안전문 전체닫힘 상태를 철저히 확인한 후 출발합니다."
        ),
        "source_doc": "6호선 응급조치 가이드-1.pptx (61b7c6ec-e756-49be-9702-9e4420e0f599) 슬라이드 28 및 운전취급규정.hwp 제46조, 제242조",
        "source_location": "가이드-1 Slide 28 / 규정 제46조, 제242조",
        "rationale": "차상 PSD 무선장치 노선모드 확인 및 전원 RESET 절차와 규정 제46조/제242조에 따른 2개역 이상 취급 시 관제보고·열차감시 조치 반영",
    },
    "guide_pantograph": {
        "reference": (
            "6호선 전동차 판토그래프 상승불능 시 운전실 제어대 EPANDS(비상전원차단스위치) 상태 및 주간제어기 역행 이외 위치를 확인하고, "
            "6100호차 운전실 AP.CBET(비상전원차단회로) 및 M1차(2호, 6호)의 AP.CBSUCC, AP.CBDO5CC, AP.CBLBC 차단기 차단 여부를 확인하여 차단 시 복귀합니다. "
            "조치 후에도 판토상승 스위치 취급 시 상승불능이면 지체 없이 운전관제에 상황을 보고합니다(규정 제35조). "
            "출고 시에는 차량교환을 요청하고, 본선 운행 중에는 최근 정거장까지 타행운행 후 정차하여 재기동 불능 시 관제 임시운전명령(규정 제74조)에 따라 구원운전 조치를 시행합니다."
        ),
        "source_doc": "6호선 응급조치 가이드-1.pptx (61b7c6ec-e756-49be-9702-9e4420e0f599) 슬라이드 35, 36 및 운전취급규정.hwp 제35조, 제74조",
        "source_location": "가이드-1 Slide 35, 36 / 규정 제35조, 제74조",
        "rationale": "EPANDS 및 관련 NFB(AP.CBET, AP.CBSUCC 등) 점검 절차와 제35조/제74조에 따른 관제 보고, 타행운행 및 구원운전 조치 명시",
    },
    "guide_emergency_brake": {
        "reference": (
            "6호선 전동차 비상제동 풀림불능 시 우선 운전모드 수동 전환 후 제동7단에서 역행을 시도하고, "
            "비상제동차단(EBCOS) 스위치 취급 후 역행 시도, 운전모드 비상 전환 후 역행 시도를 단계별로 시행합니다. "
            "점검사항으로 MR 압력이 6.5 kg/㎠ 이하인 경우 MRPS OFF를 확인하고 주공기압축기(CM) 구동 상태 및 공기배관 누설·파열을 점검하며, "
            "비상제동(EBS) 스위치 및 구원운전(ROS) 스위치 취급 상태를 확인하여 복귀합니다. 또한 전·후부Tc차 AP.CBEMBR 및 AP.CBSU1TC·2TC 차단기를 확인하여 복귀합니다. "
            "TC1·TC2 동시 고장 시에는 비상전원차단스위치(EPANDS)로 판토하강 후 약 5초 뒤 재기동을 시도하며, 최종 풀림불능 시 관제센터에 구원을 요청합니다."
        ),
        "source_doc": "6호선 응급조치 가이드-2.pptx (9fa17af6-51cc-4366-9f1e-d13b4e5b8405) 슬라이드 3, 5",
        "source_location": "가이드-2 Slide 3, 5",
        "rationale": "기존에 비상제동 일반 정의인 제25조만 참조하여 점검 절차를 담지 못하던 오류를 해결하고, 6호선 가이드 원문의 EBCOS, MRPS, NFB, 재기동 등 실무 조치를 완전하게 수록",
    },
    "guide_atc": {
        "reference": (
            "6호선 전동차 ATC 장치 고장 시 운전실 RESET S/W1·2 또는 ATC 제어차단기(AP.CBATC1·2)를 동시 차단 후 복귀하여 리셋을 시행합니다(출입문 개방 중일 때는 닫은 후 실시). "
            "ATC1 고장 시 ATC2로 자동 절체되지 않으면 S/W1 또는 AP.CBATC1을 차단합니다. "
            "복귀불능 시 운전관제에 즉시 보고하고 관제 지시에 따라 지령식 운행(운전모드 비상, 출입문모드 수/수 전환)을 시행합니다. "
            "규정 제144조에 따라 차상 ATC 고장으로 지령식을 시행하는 영업열차는 승객을 하차시키고 해당 역부터 회송 조치하며, 5~8호선에서는 차량기동반 또는 승무 지도요원이 동승하여 운전합니다."
        ),
        "source_doc": "6호선 응급조치 가이드-2.pptx (9fa17af6-51cc-4366-9f1e-d13b4e5b8405) 슬라이드 46, 47 및 운전취급규정.hwp 제144조",
        "source_location": "가이드-2 Slide 46, 47 / 규정 제144조",
        "rationale": "기존에 무관한 운전시각 기록(제34조)이 포함되어 있던 오류를 배제하고, ATC 1/2 리셋·수동절체 절차와 규정 제144조에 따른 지령식 운행, 승객 하차 및 회송, 동승자 규정을 정확히 반영",
    },
}


class KoreanAnswerRelevancePrompt(AnswerRelevancePrompt):
    """Keep answer-relevancy question generation aligned with Korean answers."""

    instruction = (
        "한국어 답변의 핵심 내용으로 답할 수 있는 한국어 질문을 생성하세요. "
        "답변이 구체적이고 정보가 있으면 noncommittal을 0, 모호하거나 회피성이면 1로 표시하세요. "
        "생성한 질문은 답변에 나온 상황과 조치의 핵심을 포함해야 합니다."
    )

    examples: ClassVar[list[tuple[AnswerRelevanceInput, AnswerRelevanceOutput]]] = [
        (
            AnswerRelevanceInput(
                response="출입문 고장으로 전체 출입문이 열리지 않을 때는 운전관제에 보고하고 안내방송과 응급조치를 실시한다."
            ),
            AnswerRelevanceOutput(
                question="출입문 고장으로 전체 출입문이 열리지 않을 때 어떤 조치를 해야 하는가?",
                noncommittal=0,
            ),
        ),
        (
            AnswerRelevanceInput(
                response="정거장 외에서 제동관 또는 공기관 고장으로 통기불능이면 운전관제에 구원을 요청한다."
            ),
            AnswerRelevanceOutput(
                question="정거장 외에서 제동관 또는 공기관 고장으로 통기불능일 때 어떻게 조치하는가?",
                noncommittal=0,
            ),
        ),
        (
            AnswerRelevanceInput(response="관련 문서에서 확인할 수 없습니다."),
            AnswerRelevanceOutput(
                question="관련 문서에서 확인할 수 없는 내용은 무엇인가?",
                noncommittal=1,
            ),
        ),
    ]


class KoreanContextRecallPrompt(ContextRecallPrompt):
    """Judge attribution in Korean without relying on the default English examples."""

    instruction = (
        "한국어 질문, 컨텍스트, 정답을 기준으로 정답의 문장을 원자적 주장으로 나누세요. "
        "각 주장이 컨텍스트에 직접 또는 의미상으로 뒷받침되면 attributed=1, "
        "컨텍스트에 없거나 모순되면 attributed=0으로 표시하세요. "
        "컨텍스트에 문장이 그대로 포함되어 있으면 반드시 1로 표시하세요."
    )

    examples: ClassVar[list[tuple[ContextRecallInput, ContextRecallOutput]]] = [
        (
            ContextRecallInput(
                question="출입문 고장 시 어떤 조치를 해야 하는가?",
                context="출입문 고장이 발생하면 운전관제에 보고하고 안내방송을 실시한다. 출입문이 정상 작동하도록 응급조치를 한다.",
                answer="운전관제에 보고한다. 안내방송을 실시한다. 출입문 정상 작동을 위한 응급조치를 한다.",
            ),
            ContextRecallOutput(
                classifications=[
                    ContextRecallClassification(
                        statement="운전관제에 보고한다.",
                        reason="컨텍스트에 직접 기재되어 있다.",
                        attributed=1,
                    ),
                    ContextRecallClassification(
                        statement="안내방송을 실시한다.",
                        reason="컨텍스트에 직접 기재되어 있다.",
                        attributed=1,
                    ),
                    ContextRecallClassification(
                        statement="응급조치를 한다.",
                        reason="컨텍스트에 의미상 기재되어 있다.",
                        attributed=1,
                    ),
                ]
            ),
        ),
    ]


class KoreanStatementGeneratorPrompt(StatementGeneratorPrompt):
    instruction = (
        "한국어 답변을 근거와 대조할 수 있는 원자적 주장으로 나누세요. "
        "각 주장은 주어를 포함하고, 답변에 없는 내용을 추가하지 마세요. 인용 표시는 주장으로 만들지 마세요."
    )

    examples: ClassVar[list[tuple[StatementGeneratorInput, StatementGeneratorOutput]]] = [
        (
            StatementGeneratorInput(
                question="차량고장으로 자력운전이 곤란하면 어떻게 해야 하는가?",
                answer="운전관제에 보고하고 구원열차를 요구한다. 구름 우려가 있으면 구름방지 조치를 한다.",
            ),
            StatementGeneratorOutput(
                statements=[
                    "운전관제에 차량고장을 보고한다.",
                    "구원열차를 요구한다.",
                    "구름 우려가 있으면 구름방지 조치를 한다.",
                ]
            ),
        ),
    ]


class KoreanNLIStatementPrompt(NLIStatementPrompt):
    instruction = (
        "한국어 컨텍스트를 기준으로 각 주장이 직접 또는 의미상 뒷받침되는지 판단하세요. "
        "뒷받침되면 verdict=1, 없거나 모순되면 verdict=0입니다. "
        "문법 형태가 다르더라도 같은 의미이고 컨텍스트에 근거가 있으면 1로 표시하세요."
    )

    examples: ClassVar[list[tuple[NLIStatementInput, NLIStatementOutput]]] = [
        (
            NLIStatementInput(
                context="차량고장이 발생하면 운전관제에 보고하고 구원열차를 요구해야 한다.",
                statements=["운전관제에 차량고장을 보고한다.", "승객에게 환불한다."],
            ),
            NLIStatementOutput(
                statements=[
                    StatementFaithfulnessAnswer(
                        statement="운전관제에 차량고장을 보고한다.",
                        reason="컨텍스트에 같은 의미가 있다.",
                        verdict=1,
                    ),
                    StatementFaithfulnessAnswer(
                        statement="승객에게 환불한다.",
                        reason="컨텍스트에 근거가 없다.",
                        verdict=0,
                    ),
                ]
            ),
        ),
    ]


def _article(text: str, number: int) -> str:
    start = text.find(f"제{number}조(")
    if start < 0:
        raise ValueError(f"제{number}조를 찾을 수 없습니다")
    next_article = re.search(r"\n제\d+조(?:\(|\s|$)", text[start + 1 :])
    end = start + 1 + next_article.start() if next_article else len(text)
    return text[start:end].strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RAGAS Evaluation Runner")
    parser.add_argument(
        "--cases",
        nargs="*",
        default=None,
        help="Specific case names to run (or 'doc', 'general', 'graph', 'all')",
    )
    parser.add_argument(
        "--reference-version",
        choices=["v1", "v2"],
        default="v2",
        help="Reference version to use: v2 (ground-truth fixed) or v1 (legacy articles)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Identifier for this evaluation run (defaults to timestamp-uuid)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing checkpoint for the run-id",
    )
    return parser.parse_args()


async def _run() -> None:
    args = parse_args()
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY가 필요합니다")

    run_id = args.run_id or f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    ref_version: Literal["v1", "v2"] = args.reference_version

    checkpoint_dir = Path("runtime/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = checkpoint_dir / f"{run_id}.json"

    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=90.0)
    evaluator_llm = llm_factory(settings.llm_model, client=client, max_tokens=8192)
    if re.match(r"^gpt-(?:[5-9]|1[0-9])(?:[.-]|$)", settings.llm_model.lower()):
        evaluator_llm.model_args.pop("max_tokens", None)
        evaluator_llm.model_args.pop("top_p", None)
        evaluator_llm.model_args["max_completion_tokens"] = 8192
        evaluator_llm.model_args["temperature"] = 1
    evaluator_embedding_model = "text-embedding-3-large"
    evaluator_embeddings = embedding_factory(
        provider="openai", model=evaluator_embedding_model, client=client
    )
    answer_relevancy = AnswerRelevancy(
        llm=evaluator_llm, embeddings=evaluator_embeddings, strictness=3
    )
    answer_relevancy.prompt = KoreanAnswerRelevancePrompt()
    faithfulness = Faithfulness(llm=evaluator_llm)
    faithfulness.statement_generator_prompt = KoreanStatementGeneratorPrompt()
    faithfulness.nli_statement_prompt = KoreanNLIStatementPrompt()
    context_recall = ContextRecall(llm=evaluator_llm)
    context_recall.prompt = KoreanContextRecallPrompt()
    answer_correctness = AnswerCorrectness(
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )
    metrics = {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "answer_correctness": answer_correctness,
        "context_precision": ContextPrecision(llm=evaluator_llm),
        "context_recall": context_recall,
    }

    def graph_probe(db, question: str) -> dict[str, Any]:
        base = rag_service.retrieve(db, question, top_k=5, max_hops=0)
        expanded = rag_service.retrieve(db, question, top_k=5, max_hops=2)
        approved_ids = set(
            db.scalars(select(DocumentLink.id).where(DocumentLink.status == "approved")).all()
        )
        base_ids = {item.fragment.id for item in base}
        expanded_ids = {item.fragment.id for item in expanded}
        linked = [item for item in expanded if item.link_id]
        approved_links_only = all(item.link_id in approved_ids for item in linked)
        return {
            "base_evidence_count": len(base),
            "expanded_evidence_count": len(expanded),
            "base_link_count": sum(bool(item.link_id) for item in base),
            "expanded_link_count": len(linked),
            "expanded_hop_count": sum(item.hop > 0 for item in expanded),
            "added_evidence_count": len(expanded_ids - base_ids),
            "approved_links_only": approved_links_only,
            "used": bool(linked) and bool(expanded_ids - base_ids) and approved_links_only,
        }

    db = SessionLocal()
    try:
        rules = db.get(DocumentContent, RULE_VERSION)
        if not rules:
            raise RuntimeError(f"규정 content를 찾을 수 없습니다: {RULE_VERSION}")
        v1_references = {
            number: _article(rules.text, number)
            for case in DOCUMENT_CASES
            for number in case.reference_articles
        }

        # Filter cases if --cases is specified
        target_doc_cases = DOCUMENT_CASES
        target_gen_cases = GENERAL_CASES

        if args.cases:
            requested = set(args.cases)
            if "all" in requested:
                pass
            elif "doc" in requested:
                target_gen_cases = []
            elif "general" in requested:
                target_doc_cases = []
            elif "graph" in requested:
                target_doc_cases = [c for c in DOCUMENT_CASES if c.graph_required]
                target_gen_cases = []
            else:
                target_doc_cases = [c for c in DOCUMENT_CASES if c.name in requested]
                target_gen_cases = [c for c in GENERAL_CASES if c.name in requested]

        # Load existing checkpoint if resume is requested
        completed_doc_rows: dict[str, dict[str, Any]] = {}
        completed_gen_rows: dict[str, dict[str, Any]] = {}
        if args.resume and checkpoint_file.exists():
            try:
                cp_data = json.loads(checkpoint_file.read_text(encoding="utf-8"))
                # Verify environment compatibility
                if (
                    cp_data.get("llm_model") == settings.llm_model
                    and cp_data.get("reference_version") == ref_version
                ):
                    for r in cp_data.get("document_cases", []):
                        completed_doc_rows[r["case"]] = r
                    for r in cp_data.get("general_cases", []):
                        completed_gen_rows[r["case"]] = r
                    print(f"Resumed checkpoint from {checkpoint_file} ({len(completed_doc_rows)} doc, {len(completed_gen_rows)} gen)")
            except (json.JSONDecodeError, OSError) as e:
                print(f"Checkpoint resume failed ({e}), starting fresh.")

        print(f"Run ID: {run_id} | Ref Version: {ref_version} | LLM: {settings.llm_model} | Embedding: {rag_service.embedding_provider.name}")
        print(f"Executing: {len(target_doc_cases)} document cases, {len(target_gen_cases)} general cases\n" + "=" * 80)

        document_rows: list[dict[str, Any]] = []
        for case in target_doc_cases:
            if case.name in completed_doc_rows:
                row = completed_doc_rows[case.name]
                document_rows.append(row)
                print(f"[REUSED] {case.name}: mode={row['mode']}, faithfulness={row.get('faithfulness', 0):.4f}, correctness={row.get('answer_correctness', 0):.4f}")
                continue

            if ref_version == "v2" and case.name in REFERENCE_V2:
                ref_info = REFERENCE_V2[case.name]
                reference = ref_info["reference"]
                ref_source = ref_info["source_doc"] + " - " + ref_info["source_location"]
            else:
                reference = "\n\n".join(v1_references[number] for number in case.reference_articles)
                ref_source = f"운전취급규정 {case.reference_articles}조"

            result = chat_service.respond(db, case.question, [])
            evidence = result.evidence
            contexts = [
                item.fragment.text or ""
                for item in evidence
                if (item.fragment.text or "").strip()
            ]
            scores: dict[str, float] = {}
            scores["answer_relevancy"] = (
                await metrics["answer_relevancy"].ascore(
                    user_input=case.question, response=result.answer
                )
            ).value
            scores["answer_correctness"] = (
                await metrics["answer_correctness"].ascore(
                    user_input=case.question,
                    response=result.answer,
                    reference=reference,
                )
            ).value
            if contexts:
                scores["faithfulness"] = (
                    await metrics["faithfulness"].ascore(
                        user_input=case.question,
                        response=result.answer,
                        retrieved_contexts=contexts,
                    )
                ).value
                scores["context_precision"] = (
                    await metrics["context_precision"].ascore(
                        user_input=case.question,
                        reference=reference,
                        retrieved_contexts=contexts,
                    )
                ).value
                scores["context_recall"] = (
                    await metrics["context_recall"].ascore(
                        user_input=case.question,
                        reference=reference,
                        retrieved_contexts=contexts,
                    )
                ).value
            else:
                scores.update(
                    faithfulness=0.0,
                    context_precision=0.0,
                    context_recall=0.0,
                )

            evidence_details = [
                {
                    "hop": item.hop,
                    "score": round(item.score, 4),
                    "link_id": item.link_id,
                    "relation": item.via_relation,
                    "location": item.location,
                    "locator": item.fragment.locator_json,
                    "text_snippet": (item.fragment.text or "")[:100].replace("\n", " "),
                }
                for item in evidence
            ]

            row: dict[str, Any] = {
                "case": case.name,
                "question": case.question,
                "expected_articles": list(case.reference_articles),
                "reference": reference,
                "reference_source": ref_source,
                "response": result.answer,
                "mode": result.mode,
                "context_count": len(contexts),
                "chat_link_count": sum(bool(item.link_id) for item in evidence),
                "chat_hop_count": sum(item.hop > 0 for item in evidence),
                "evidence_details": evidence_details,
                **scores,
            }

            if case.graph_required:
                probe = graph_probe(db, case.question)
                chat_used = bool(result.evidence) and any(
                    item.hop > 0 or item.link_id for item in result.evidence
                )
                row["graph_check"] = {
                    **probe,
                    "chat_used": chat_used,
                    "passed": bool(probe["used"]) and chat_used,
                }

            document_rows.append(row)
            completed_doc_rows[case.name] = row

            print(
                f"[DONE] {case.name}: mode={result.mode}, contexts={len(contexts)} | "
                + " | ".join(f"{k}={scores[k]:.4f}" for k in ("faithfulness", "answer_relevancy", "answer_correctness", "context_precision", "context_recall"))
            )
            if case.graph_required:
                check = row["graph_check"]
                print(
                    f"       ↳ graph: chat_links={row['chat_link_count']}, "
                    f"probe_links={check['expanded_link_count']}, "
                    f"added={check['added_evidence_count']}, passed={check['passed']}"
                )

            # Save checkpoint immediately
            checkpoint_data = {
                "run_id": run_id,
                "llm_model": settings.llm_model,
                "reference_version": ref_version,
                "updated_at_utc": datetime.now(UTC).isoformat(),
                "document_cases": document_rows,
                "general_cases": list(completed_gen_rows.values()),
            }
            checkpoint_file.write_text(json.dumps(checkpoint_data, ensure_ascii=False, indent=2), encoding="utf-8")

        general_rows: list[dict[str, Any]] = []
        for case in target_gen_cases:
            if case.name in completed_gen_rows:
                row = completed_gen_rows[case.name]
                general_rows.append(row)
                print(f"[REUSED] {case.name}: mode={row['mode']}, correctness={row.get('answer_correctness', 0):.4f}")
                continue

            result = chat_service.respond(db, case.question, [])
            scores = {
                "answer_correctness": (
                    await metrics["answer_correctness"].ascore(
                        user_input=case.question,
                        response=result.answer,
                        reference=case.reference,
                    )
                ).value,
                "answer_relevancy": (
                    await metrics["answer_relevancy"].ascore(
                        user_input=case.question, response=result.answer
                    )
                ).value,
            }
            row = {
                "case": case.name,
                "question": case.question,
                "reference": case.reference,
                "response": result.answer,
                "mode": result.mode,
                "evidence_count": len(result.evidence),
                "routing_pass": result.mode == "general" and not result.evidence,
                **scores,
            }
            general_rows.append(row)
            completed_gen_rows[case.name] = row

            print(
                f"[DONE] {case.name}: mode={result.mode}, evidence={len(result.evidence)} | "
                + " | ".join(f"{k}={scores[k]:.4f}" for k in ("answer_correctness", "answer_relevancy"))
            )

            # Save checkpoint immediately
            checkpoint_data = {
                "run_id": run_id,
                "llm_model": settings.llm_model,
                "reference_version": ref_version,
                "updated_at_utc": datetime.now(UTC).isoformat(),
                "document_cases": document_rows,
                "general_cases": general_rows,
            }
            checkpoint_file.write_text(json.dumps(checkpoint_data, ensure_ascii=False, indent=2), encoding="utf-8")

        # Aggregations
        document_metric_names = (
            "faithfulness",
            "answer_relevancy",
            "answer_correctness",
            "context_precision",
            "context_recall",
        )
        general_metric_names = ("answer_correctness", "answer_relevancy")

        direct_doc_rows = [r for r in document_rows if "graph_check" not in r]
        graph_doc_rows = [r for r in document_rows if "graph_check" in r]
        knowledge_gen_rows = [r for r in general_rows if r["case"] != "greeting"]

        averages: dict[str, dict[str, float]] = {}
        if document_rows:
            averages["document"] = {
                key: sum(float(r[key]) for r in document_rows) / len(document_rows)
                for key in document_metric_names
            }
        if direct_doc_rows:
            averages["document_direct"] = {
                key: sum(float(r[key]) for r in direct_doc_rows) / len(direct_doc_rows)
                for key in document_metric_names
            }
        if graph_doc_rows:
            averages["document_graph"] = {
                key: sum(float(r[key]) for r in graph_doc_rows) / len(graph_doc_rows)
                for key in document_metric_names
            }
        if general_rows:
            averages["general"] = {
                key: sum(float(r[key]) for r in general_rows) / len(general_rows)
                for key in general_metric_names
            }
        if knowledge_gen_rows:
            averages["general_knowledge"] = {
                key: sum(float(r[key]) for r in knowledge_gen_rows) / len(knowledge_gen_rows)
                for key in general_metric_names
            }

        graph_passed = sum(bool(r.get("graph_check", {}).get("passed")) for r in graph_doc_rows)
        greeting_passed = any(r["case"] == "greeting" and r["routing_pass"] for r in general_rows)

        # Check target satisfaction
        doc_targets_met = bool(
            averages.get("document")
            and all(averages["document"][m] >= 0.9 for m in document_metric_names)
        )
        gen_targets_met = bool(
            averages.get("general_knowledge")
            and all(averages["general_knowledge"][m] >= 0.9 for m in general_metric_names)
        )
        all_targets_met = doc_targets_met and gen_targets_met and greeting_passed and (graph_passed == len(graph_doc_rows))
        evaluation_complete = len(document_rows) == len(DOCUMENT_CASES) and len(general_rows) == len(GENERAL_CASES)

        payload = {
            "run_id": run_id,
            "evaluated_at_utc": datetime.now(UTC).isoformat(),
            "dataset_version": DATASET_VERSION,
            "reference_version": ref_version,
            "embedding_provider": rag_service.embedding_provider.name,
            "embedding_model": rag_service.embedding_provider.model,
            "evaluator_embedding_model": evaluator_embedding_model,
            "llm_model": settings.llm_model,
            "evaluation_complete": evaluation_complete,
            "targets_met": all_targets_met,
            "document_case_count": len(document_rows),
            "general_case_count": len(general_rows),
            "document_cases": document_rows,
            "general_cases": general_rows,
            "graph_check": {
                "case_count": len(graph_doc_rows),
                "passed_count": graph_passed,
                "all_passed": graph_passed == len(graph_doc_rows),
            },
            "greeting_check": {
                "passed": greeting_passed,
            },
            "averages": averages,
        }

        output = Path("runtime/ragas_results.json")
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        # Also keep run-specific results archive
        archive_file = Path(f"runtime/ragas_results_{run_id}.json")
        archive_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY:")
        print(f"Run ID: {run_id} | Reference Version: {ref_version} | Evaluation Complete: {evaluation_complete}")
        if "document" in averages:
            print("Document Cases Average (17 cases):")
            for m in document_metric_names:
                status = "PASS" if averages["document"][m] >= 0.9 else "FAIL"
                print(f"  - {m:20s}: {averages['document'][m]:.4f} [{status}]")
        if "general_knowledge" in averages:
            print("General Knowledge Average (4 cases, greeting excluded):")
            for m in general_metric_names:
                status = "PASS" if averages["general_knowledge"][m] >= 0.9 else "FAIL"
                print(f"  - {m:20s}: {averages['general_knowledge'][m]:.4f} [{status}]")
        print(f"Graph check: {graph_passed}/{len(graph_doc_rows)} passed")
        print(f"Greeting check: {'PASS' if greeting_passed else 'FAIL'}")
        print(f"Targets met: {'YES (COMPLETED)' if all_targets_met else 'NO (INCOMPLETE)'}")
        print(f"Saved: {output.resolve()} and {archive_file.resolve()}")
    finally:
        db.close()
        await client.close()


if __name__ == "__main__":
    asyncio.run(_run())
