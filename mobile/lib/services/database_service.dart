import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/scan_record.dart';

class DatabaseService {
  static Database? _db;

  Future<Database> get db async {
    _db ??= await _init();
    return _db!;
  }

  Future<Database> _init() async {
    final path = join(await getDatabasesPath(), 'flashport.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, _) => db.execute('''
        CREATE TABLE scan_records (
          scan_id TEXT PRIMARY KEY,
          document_type TEXT NOT NULL,
          ml_kit_text TEXT,
          image_path TEXT,
          scanned_at TEXT NOT NULL,
          status INTEGER DEFAULT 0,
          server_response TEXT
        )
      '''),
    );
  }

  Future<void> insert(ScanRecord record) async {
    final d = await db;
    await d.insert('scan_records', record.toMap(),
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<void> updateStatus(String scanId, SyncStatus status,
      {Map<String, dynamic>? response}) async {
    final d = await db;
    final values = <String, dynamic>{'status': status.index};
    if (response != null) {
      values['server_response'] = jsonEncode(response);
    }
    await d.update('scan_records', values,
        where: 'scan_id = ?', whereArgs: [scanId]);
  }

  Future<List<ScanRecord>> getPending() async {
    final d = await db;
    // Also retry records stuck in `syncing` (app closed mid-upload) or `failed` (server error).
    final retryStatuses = [
      SyncStatus.pendingSync.index,
      SyncStatus.syncing.index,
      SyncStatus.failed.index,
    ].join(',');
    final rows = await d.query('scan_records',
        where: 'status IN ($retryStatuses)');
    return rows.map(ScanRecord.fromMap).toList();
  }

  Future<void> delete(String scanId) async {
    final d = await db;
    await d.delete('scan_records', where: 'scan_id = ?', whereArgs: [scanId]);
  }

  Future<List<ScanRecord>> getAll() async {
    final d = await db;
    final rows =
        await d.query('scan_records', orderBy: 'scanned_at DESC', limit: 50);
    return rows.map(ScanRecord.fromMap).toList();
  }
}
