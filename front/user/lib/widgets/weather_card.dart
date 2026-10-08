import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../core/colors.dart';
import 'app_card.dart';

class WeatherCard extends StatefulWidget {
  const WeatherCard({super.key});

  @override
  State<WeatherCard> createState() => _WeatherCardState();
}

class _WeatherCardState extends State<WeatherCard> {
  bool _isLoading = true;
  String _temperature = '-';
  String _weatherCode = '0';
  String _precipProb = '-';
  String _pm10 = '-';
  String _pm25 = '-';

  @override
  void initState() {
    super.initState();
    _fetchWeather();
  }

  Future<void> _fetchWeather() async {
    final prefs = await SharedPreferences.getInstance();
    final cacheKey = 'weather_cache';
    final cacheTimeKey = 'weather_cache_time';
    
    final lastTimeStr = prefs.getString(cacheTimeKey);
    final cachedData = prefs.getString(cacheKey);
    
    if (lastTimeStr != null && cachedData != null) {
      final lastTime = DateTime.parse(lastTimeStr);
      if (DateTime.now().difference(lastTime).inMinutes < 30) {
        _applyData(jsonDecode(cachedData));
        return;
      }
    }

    try {
      final weatherRes = await http.get(Uri.parse(
          'https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.978&current=temperature_2m,weather_code&daily=precipitation_probability_max&forecast_days=1&timezone=Asia%2FSeoul'));
      final airRes = await http.get(Uri.parse(
          'https://air-quality-api.open-meteo.com/v1/air-quality?latitude=37.5665&longitude=126.978&current=pm10,pm2_5&timezone=Asia%2FSeoul'));

      if (weatherRes.statusCode == 200 && airRes.statusCode == 200) {
        final weatherJson = jsonDecode(weatherRes.body);
        final airJson = jsonDecode(airRes.body);

        final data = {
          'temp': weatherJson['current']['temperature_2m'].toString(),
          'code': weatherJson['current']['weather_code'].toString(),
          'precip': weatherJson['daily']['precipitation_probability_max'][0].toString(),
          'pm10': airJson['current']['pm10'].toString(),
          'pm25': airJson['current']['pm2_5'].toString(),
        };

        prefs.setString(cacheKey, jsonEncode(data));
        prefs.setString(cacheTimeKey, DateTime.now().toIso8601String());
        
        _applyData(data);
      } else if (mounted) {
        setState(() => _isLoading = false);
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _applyData(Map<String, dynamic> data) {
    if (mounted) {
      setState(() {
        _temperature = data['temp'];
        _weatherCode = data['code'];
        _precipProb = data['precip'];
        _pm10 = data['pm10'];
        _pm25 = data['pm25'];
        _isLoading = false;
      });
    }
  }

  String _getWeatherDesc(String code) {
    switch (code) {
      case '0': return '맑음';
      case '1':
      case '2':
      case '3': return '구름';
      case '45':
      case '48': return '안개';
      case '51':
      case '53':
      case '55':
      case '61':
      case '63':
      case '65': return '비';
      case '71':
      case '73':
      case '75': return '눈';
      case '95':
      case '96':
      case '99': return '뇌우';
      default: return '맑음';
    }
  }

  IconData _getWeatherIcon(String code) {
    switch (code) {
      case '0': return Icons.wb_sunny;
      case '1':
      case '2':
      case '3': return Icons.cloud;
      case '45':
      case '48': return Icons.foggy;
      case '51':
      case '53':
      case '55':
      case '61':
      case '63':
      case '65': return Icons.water_drop;
      case '71':
      case '73':
      case '75': return Icons.ac_unit;
      default: return Icons.wb_sunny;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const AppCard(
        child: Center(child: CircularProgressIndicator()),
      );
    }

    return AppCard(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 12,
        runSpacing: 8,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(_getWeatherIcon(_weatherCode), color: AppColors.line6Gold, size: 28),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('서울 날씨', style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
                  Text('${_getWeatherDesc(_weatherCode)} $_temperature°C', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.ink)),
                ],
              ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('강수확률 $_precipProb%', style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
              Text('미세먼지 $_pm10 / 초미세 $_pm25', style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
            ],
          ),
        ],
      ),
    );
  }
}
