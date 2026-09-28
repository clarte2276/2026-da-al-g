// Start back/tests/serve_link_qa.py and its --ui mode first. Requires Playwright.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE || "playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  const artifacts = path.resolve(__dirname, "../../../back/runtime/link-qa");
  fs.mkdirSync(artifacts, { recursive: true });
  try {
    await page.goto("http://127.0.0.1:15173");
    async function showExplorer() {
      if (!await page.locator(".explorer-section").evaluate(node => node.open)) {
        await page.locator(".explorer-section > summary").click();
      }
    }
    const row = name => page.locator(".file-row").filter({ has: page.getByText(name, { exact: true }) });
    await row("01-text.docx").getByRole("button", { name: "왼쪽", exact: true }).click();
    await page.locator(".continuous-text").waitFor();
    assert((await page.locator(".continuous-text").textContent()).endsWith("마지막 문장"));
    await page.locator(".continuous-text").focus();
    await page.keyboard.press("Control+Home");
    for (let i = 0; i < 3; i++) await page.keyboard.press("Shift+ArrowRight");
    assert.equal(await page.evaluate(() => window.getSelection().toString()), "ATC");
    await row("02-pages.pdf").getByRole("button", { name: "오른쪽", exact: true }).click();
    await page.locator(".page-stage canvas").waitFor();
    const textPane = page.locator(".selection-viewer").first();
    await textPane.getByRole("textbox", { name: "본문 찾기" }).fill("ATC 고장 조치");
    await textPane.getByRole("button", { name: "다음 찾기" }).click();
    await textPane.getByRole("button", { name: "구절 지정", exact: true }).click();
    assert.equal(await page.locator(".continuous-text mark").textContent(), "ATC 고장 조치");
    await page.getByRole("checkbox", { name: "1 페이지 선택", exact: true }).check();
    await page.getByRole("button", { name: "다음", exact: true }).click();
    await page.getByRole("button", { name: "다음", exact: true }).click();
    await page.getByRole("button", { name: "이 페이지 선택", exact: true }).click();
    assert.equal(await page.locator(".selected-pages > div").count(), 2);
    await page.getByRole("button", { name: "연결 저장", exact: true }).click();
    await page.getByText("연결 1건을 초안으로 저장했습니다.", { exact: false }).waitFor();
    await page.screenshot({ path: path.join(artifacts, "text-pages.png"), fullPage: true });
    await page.getByRole("button", { name: "연결 검토", exact: true }).click();
    const link = page.locator(".review-link").first();
    await link.getByRole("button", { name: "승인", exact: true }).click();
    await page.getByText("연결을 승인했습니다.", { exact: true }).waitFor();
    await page.getByRole("combobox", { name: "연결 상태" }).selectOption("approved");
    await page.locator(".review-link").first().getByRole("button", { name: "선택 확인·수정" }).click();
    await page.locator(".continuous-text mark").waitFor();
    assert.equal(await page.locator(".continuous-text mark").textContent(), "ATC 고장 조치");
    assert.equal(await page.locator(".selected-pages > div").count(), 2);
    await page.getByRole("button", { name: "검색 검증", exact: true }).click();
    await page.getByRole("textbox", { name: "질문", exact: true }).fill("ATC 고장 조치");
    await page.getByRole("button", { name: "검색", exact: true }).click();
    await page.getByRole("button", { name: "연결된 원문 확인" }).first().waitFor();
    await page.screenshot({ path: path.join(artifacts, "search-evidence.png"), fullPage: true });
    await page.getByRole("button", { name: "문서 연결", exact: true }).click();
    await page.getByRole("button", { name: "새 연결", exact: true }).click();
    await showExplorer();
    await row("03-slides.pptx").getByRole("button", { name: "오른쪽", exact: true }).click();
    await page.getByRole("button", { name: "이 슬라이드 선택", exact: true }).waitFor();
    await page.getByRole("button", { name: "이 슬라이드 선택", exact: true }).click();
    await page.getByRole("button", { name: "다음", exact: true }).click();
    await page.getByRole("button", { name: "다음", exact: true }).click();
    await page.getByRole("button", { name: "이 슬라이드 선택", exact: true }).click();
    assert.equal(await page.locator(".selected-pages > div").count(), 2);
    // Use a real DOM Range spanning paragraphs; the UI receives the ordinary mouseup event.
    const quote = await page.locator(".continuous-text").evaluate(root => {
      const node = root.firstChild;
      const start = node.textContent.indexOf("조치");
      const end = node.textContent.indexOf("중간") + 2;
      const range = document.createRange(); range.setStart(node, start); range.setEnd(node, end);
      const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
      root.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
      return range.toString();
    });
    await textPane.getByRole("button", { name: "구절 지정", exact: true }).click();
    assert(quote.includes("😀") && quote.includes("\n\n"));
    assert.equal(await page.locator(".continuous-text mark").textContent(), quote);
    await page.getByRole("button", { name: "연결 저장", exact: true }).click();
    await page.getByText("연결 1건을 초안으로 저장했습니다.", { exact: false }).waitFor();
    await page.screenshot({ path: path.join(artifacts, "text-slides.png"), fullPage: true });
    for (const filename of ["sample.hwpx", "sample.hwp"]) {
      await showExplorer();
      await row(filename).getByRole("button", { name: "왼쪽", exact: true }).click();
      await page.locator(".selection-viewer").first().getByRole("heading", { name: filename, exact: true }).waitFor();
      assert((await page.locator(".continuous-text").textContent()).trim().length > 0);
    }
    await page.setViewportSize({ width: 760, height: 1000 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    assert.deepEqual(errors, []);
    console.log("PASS: text range, PDF/PPTX page groups, save, approval, reload, graph evidence; no page errors.");
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
