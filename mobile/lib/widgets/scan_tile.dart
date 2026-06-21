import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/scan_record.dart';
import '../screens/result_screen.dart';

class ScanTile extends StatelessWidget {
  final ScanRecord record;

  const ScanTile({super.key, required this.record});

  @override
  Widget build(BuildContext context) {
    final isSynced = record.status == SyncStatus.synced;
    final serverResponse = record.serverResponse;
    final riskBadge = serverResponse?['risk_badge'] as String?;
    final riskScore = serverResponse?['risk_score'] as int?;
    final fields = serverResponse?['extracted_fields'] as Map<String, dynamic>?;
    final hsCode = fields?['hs_code'] as String?;
    final importer = fields?['importer'] as String?;

    return GestureDetector(
      onTap: isSynced && serverResponse != null
          ? () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => ResultScreen(response: serverResponse),
                ),
              )
          : null,
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF161B22),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: _borderColour(riskBadge).withValues(alpha: 0.3), width: 1),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              // Status icon
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _statusColour(riskBadge).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(_icon(riskBadge), color: _statusColour(riskBadge), size: 22),
              ),
              const SizedBox(width: 14),

              // Content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      record.documentType.label,
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      DateFormat('dd MMM yyyy, HH:mm').format(record.scannedAt),
                      style: const TextStyle(color: Colors.white38, fontSize: 12),
                    ),
                    if (isSynced && (hsCode != null || importer != null)) ...[
                      const SizedBox(height: 3),
                      Text(
                        _summaryLine(hsCode, importer),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Colors.white38, fontSize: 11),
                      ),
                    ] else if (!isSynced && record.mlKitText.isNotEmpty) ...[
                      const SizedBox(height: 3),
                      Text(
                        record.mlKitText.replaceAll('\n', ' ').trim(),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Colors.white24, fontSize: 11),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 8),

              // Right-side badge
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  if (isSynced && riskBadge != null)
                    _RiskBadge(riskBadge: riskBadge, riskScore: riskScore)
                  else
                    _StatusChip(status: record.status),
                  if (isSynced)
                    const Padding(
                      padding: EdgeInsets.only(top: 4),
                      child: Icon(Icons.chevron_right, color: Colors.white24, size: 16),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _summaryLine(String? hsCode, String? importer) {
    if (hsCode != null && importer != null) return 'HS: $hsCode · $importer';
    if (hsCode != null) return 'HS Code: $hsCode';
    if (importer != null) return importer;
    return '';
  }

  Color _statusColour(String? riskBadge) {
    if (record.status == SyncStatus.synced) {
      return switch (riskBadge) {
        'green' => Colors.green,
        'red' => Colors.red,
        _ => Colors.orange,
      };
    }
    return switch (record.status) {
      SyncStatus.syncing => Colors.blue,
      SyncStatus.failed => Colors.red,
      _ => Colors.orange,
    };
  }

  Color _borderColour(String? riskBadge) => _statusColour(riskBadge);

  IconData _icon(String? riskBadge) {
    if (record.status == SyncStatus.synced) {
      return switch (riskBadge) {
        'green' => Icons.check_circle_outline,
        'red' => Icons.warning_rounded,
        _ => Icons.info_outline,
      };
    }
    return switch (record.status) {
      SyncStatus.syncing => Icons.sync,
      SyncStatus.failed => Icons.error_outline,
      _ => Icons.schedule,
    };
  }
}

class _RiskBadge extends StatelessWidget {
  final String riskBadge;
  final int? riskScore;

  const _RiskBadge({required this.riskBadge, this.riskScore});

  @override
  Widget build(BuildContext context) {
    final (label, colour) = switch (riskBadge) {
      'green' => ('Hijau', Colors.green),
      'red' => ('Merah', Colors.red),
      _ => ('Kuning', Colors.orange),
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: colour.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: colour.withValues(alpha: 0.3)),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: colour.withValues(alpha: 0.9),
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        if (riskScore != null) ...[
          const SizedBox(height: 2),
          Text(
            '$riskScore%',
            style: TextStyle(color: colour.withValues(alpha: 0.6), fontSize: 10),
          ),
        ],
      ],
    );
  }
}

class _StatusChip extends StatelessWidget {
  final SyncStatus status;

  const _StatusChip({required this.status});

  @override
  Widget build(BuildContext context) {
    final (label, colour) = switch (status) {
      SyncStatus.synced => ('Synced', Colors.green),
      SyncStatus.syncing => ('Syncing…', Colors.blue),
      SyncStatus.failed => ('Failed', Colors.red),
      SyncStatus.pendingSync => ('Pending', Colors.orange),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: colour.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: colour.withValues(alpha: 0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: colour.withValues(alpha: 0.9),
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
