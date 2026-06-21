import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'backend_config.dart';

const _apiKey = String.fromEnvironment('API_KEY', defaultValue: 'changeme');

class OperatorService {
  final BackendConfig _config;

  OperatorService(this._config);

  static const _keyToken = 'op_token';
  static const _keyEmployeeId = 'op_employee_id';
  static const _keyName = 'op_name';

  Future<bool> get isLoggedIn async {
    final prefs = await SharedPreferences.getInstance();
    return (prefs.getString(_keyToken) ?? '').isNotEmpty;
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyToken);
  }

  Future<String> getName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyName) ?? '';
  }

  Future<String> getEmployeeId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyEmployeeId) ?? '';
  }

  // Returns null on success, error message string on failure.
  Future<String?> login(String employeeId, String pin) async {
    try {
      final response = await http
          .post(
            Uri.parse('${_config.url}/auth/operator/login'),
            headers: {'Content-Type': 'application/json', 'X-API-Key': _apiKey},
            body: jsonEncode({'employee_id': employeeId.trim(), 'pin': pin.trim()}),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        await _saveSession(
          token: data['access_token'] as String,
          employeeId: data['employee_id'] as String,
          name: data['name'] as String,
        );
        return null;
      }
      if (response.statusCode == 401) return 'Invalid employee ID or PIN';
      return 'Server error (${response.statusCode})';
    } on Exception catch (e) {
      return 'Cannot connect to server: $e';
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyToken);
    await prefs.remove(_keyEmployeeId);
    await prefs.remove(_keyName);
  }

  Future<void> _saveSession({
    required String token,
    required String employeeId,
    required String name,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyToken, token);
    await prefs.setString(_keyEmployeeId, employeeId);
    await prefs.setString(_keyName, name);
  }
}
