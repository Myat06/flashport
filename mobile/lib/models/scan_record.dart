import 'dart:convert';

enum SyncStatus { pendingSync, syncing, synced, failed }

enum DocumentType {
  commercialInvoice,
  billOfLading,
  packingList;

  String get apiValue => switch (this) {
        DocumentType.commercialInvoice => 'commercial_invoice',
        DocumentType.billOfLading => 'bill_of_lading',
        DocumentType.packingList => 'packing_list',
      };

  String get label => switch (this) {
        DocumentType.commercialInvoice => 'Commercial Invoice',
        DocumentType.billOfLading => 'Bill of Lading',
        DocumentType.packingList => 'Packing List',
      };
}

class ScanRecord {
  final String scanId;
  final DocumentType documentType;
  final String mlKitText;
  final String imagePath;
  final DateTime scannedAt;
  SyncStatus status;
  Map<String, dynamic>? serverResponse;

  ScanRecord({
    required this.scanId,
    required this.documentType,
    required this.mlKitText,
    required this.imagePath,
    required this.scannedAt,
    this.status = SyncStatus.pendingSync,
    this.serverResponse,
  });

  Map<String, dynamic> toMap() => {
        'scan_id': scanId,
        'document_type': documentType.apiValue,
        'ml_kit_text': mlKitText,
        'image_path': imagePath,
        'scanned_at': scannedAt.toIso8601String(),
        'status': status.index,
        'server_response': serverResponse != null ? jsonEncode(serverResponse) : null,
      };

  factory ScanRecord.fromMap(Map<String, dynamic> map) => ScanRecord(
        scanId: map['scan_id'],
        documentType: DocumentType.values.firstWhere(
          (e) => e.apiValue == map['document_type'],
          orElse: () => DocumentType.commercialInvoice,
        ),
        mlKitText: map['ml_kit_text'] ?? '',
        imagePath: map['image_path'] ?? '',
        scannedAt: DateTime.parse(map['scanned_at']),
        status: SyncStatus.values[map['status'] ?? 0],
        serverResponse: map['server_response'] != null
            ? jsonDecode(map['server_response'])
            : null,
      );
}
