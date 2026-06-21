import 'dart:convert';
import 'dart:io';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:http/http.dart' as http;
import '../models/scan_record.dart';
import 'backend_config.dart';
import 'database_service.dart';
import 'operator_service.dart';

const _apiKey = String.fromEnvironment('API_KEY', defaultValue: 'changeme');

class SyncService {
  final DatabaseService _db;
  final OperatorService _operator;
  final BackendConfig _config;

  // Increments whenever one or more records finish syncing. HomeScreen listens to this.
  final syncCount = ValueNotifier<int>(0);

  SyncService(this._db, this._operator, this._config);

  Future<void> syncPending() async {
    final pending = await _db.getPending();
    int synced = 0;
    for (final record in pending) {
      await _syncOne(record, onSynced: () => synced++);
    }
    if (synced > 0) syncCount.value++;
  }

  // Saves the record to DB and attempts immediate sync.
  // Returns the server response if sync succeeded, null if offline/failed (record stays pending).
  Future<Map<String, dynamic>?> syncOneNow(ScanRecord record) async {
    await _db.insert(record);
    try {
      final compressed = await _compress(record.imagePath);
      final imageB64 = base64Encode(compressed);
      final operatorId = await _operator.getEmployeeId();
      final fcmToken = await FirebaseMessaging.instance.getToken();

      final payload = {
        'scan_id': record.scanId,
        'scanned_at': record.scannedAt.toIso8601String(),
        'document_type': record.documentType.apiValue,
        'operator_id': operatorId.isEmpty ? null : operatorId,
        'fcm_token': fcmToken,
        'ml_kit_text': record.mlKitText,
        'image_b64': imageB64,
      };

      final response = await http
          .post(
            Uri.parse('${_config.url}/sync'),
            headers: {'Content-Type': 'application/json', ...await _authHeaders()},
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final serverResponse = jsonDecode(response.body) as Map<String, dynamic>;
        await _db.updateStatus(record.scanId, SyncStatus.synced, response: serverResponse);
        try { File(record.imagePath).deleteSync(); } catch (_) {}
        return serverResponse;
      }
      await _db.updateStatus(record.scanId, SyncStatus.pendingSync);
      return null;
    } catch (e) {
      // ignore: avoid_print
      print('[SyncService] syncOneNow error: $e  url=${_config.url}');
      await _db.updateStatus(record.scanId, SyncStatus.pendingSync);
      return null;
    }
  }

  Future<Map<String, String>> _authHeaders() async {
    final token = await _operator.getToken();
    if (token != null && token.isNotEmpty) return {'Authorization': 'Bearer $token'};
    return {'X-API-Key': _apiKey};
  }

  Future<void> _syncOne(ScanRecord record, {VoidCallback? onSynced}) async {
    await _db.updateStatus(record.scanId, SyncStatus.syncing);
    try {
      final compressed = await _compress(record.imagePath);
      final imageB64 = base64Encode(compressed);
      final operatorId = await _operator.getEmployeeId();
      final fcmToken = await FirebaseMessaging.instance.getToken();

      final payload = {
        'scan_id': record.scanId,
        'scanned_at': record.scannedAt.toIso8601String(),
        'document_type': record.documentType.apiValue,
        'operator_id': operatorId.isEmpty ? null : operatorId,
        'fcm_token': fcmToken,
        'ml_kit_text': record.mlKitText,
        'image_b64': imageB64,
      };

      final response = await http
          .post(
            Uri.parse('${_config.url}/sync'),
            headers: {'Content-Type': 'application/json', ...await _authHeaders()},
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final serverResponse = jsonDecode(response.body) as Map<String, dynamic>;
        await _db.updateStatus(record.scanId, SyncStatus.synced, response: serverResponse);
        try { File(record.imagePath).deleteSync(); } catch (_) {}
        onSynced?.call();
      } else {
        // ignore: avoid_print
        print('[SyncService] Server error ${response.statusCode}: ${response.body}');
        await _db.updateStatus(record.scanId, SyncStatus.pendingSync);
      }
    } catch (e) {
      // ignore: avoid_print
      print('[SyncService] Connection error: $e');
      await _db.updateStatus(record.scanId, SyncStatus.pendingSync);
    }
  }

  Future<List<int>> _compress(String path) async {
    if (path.toLowerCase().endsWith('.pdf')) return File(path).readAsBytesSync();
    final result = await FlutterImageCompress.compressWithFile(
      path, quality: 75, minWidth: 1280, minHeight: 720,
    );
    return result ?? File(path).readAsBytesSync();
  }
}
