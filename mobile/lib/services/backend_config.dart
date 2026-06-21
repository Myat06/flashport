import 'dart:io';
import 'package:shared_preferences/shared_preferences.dart';

class BackendConfig {
  static const _prefKey = 'backend_url';

  late String _url;

  String get url => _url;

  static String get platformDefault {
    if (Platform.isIOS) return 'http://localhost:8000';
    if (Platform.isAndroid) return 'http://10.0.2.2:8000';
    return 'http://localhost:8000';
  }

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _url = prefs.getString(_prefKey) ?? platformDefault;
  }

  Future<void> setUrl(String url) async {
    final trimmed = url.trim().replaceAll(RegExp(r'/+$'), '');
    _url = trimmed;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKey, trimmed);
  }

  Future<void> reset() async {
    _url = platformDefault;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_prefKey);
  }
}
