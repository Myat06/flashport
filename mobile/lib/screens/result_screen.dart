import 'package:flutter/material.dart';

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> response;

  const ResultScreen({super.key, required this.response});

  @override
  Widget build(BuildContext context) {
    final confidence = response['confidence_badge'] as String? ?? 'medium';
    final riskScore = response['risk_score'] as int? ?? 0;
    final riskBadge = response['risk_badge'] as String? ?? 'yellow';
    final ceisaReady = response['ceisa_ready'] as bool? ?? false;
    final flagged = (response['flagged_fields'] as List?)?.cast<String>() ?? [];
    final fields = response['extracted_fields'] as Map<String, dynamic>? ?? {};

    final (badgeColour, badgeLabel, badgeIcon) = switch (riskBadge) {
      'green' => (Colors.green, 'Low Risk — Jalur Hijau', Icons.check_circle),
      'red' => (Colors.red, 'High Risk — Jalur Merah', Icons.warning_rounded),
      _ => (Colors.orange, 'Medium Risk — Jalur Kuning', Icons.info_rounded),
    };

    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('Sync Result'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Risk summary card
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: badgeColour.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: badgeColour.withValues(alpha: 0.3)),
              ),
              child: Column(
                children: [
                  Icon(badgeIcon, color: badgeColour, size: 48),
                  const SizedBox(height: 12),
                  Text(badgeLabel,
                      style: TextStyle(
                          color: badgeColour,
                          fontSize: 18,
                          fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Text('Risk Score: $riskScore%',
                      style: TextStyle(color: badgeColour.withValues(alpha: 0.8))),
                  const SizedBox(height: 8),
                  LinearProgressIndicator(
                    value: riskScore / 100,
                    backgroundColor: Colors.white12,
                    valueColor: AlwaysStoppedAnimation<Color>(badgeColour),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Badges row
            Row(
              children: [
                _Badge(
                  label: 'OCR Confidence',
                  value: confidence.toUpperCase(),
                  colour: switch (confidence) {
                    'high' => Colors.blue,
                    'low' => Colors.red,
                    _ => Colors.orange,
                  },
                ),
                const SizedBox(width: 12),
                _Badge(
                  label: 'CEISA Ready',
                  value: ceisaReady ? 'YES' : 'NO',
                  colour: ceisaReady ? Colors.green : Colors.orange,
                ),
              ],
            ),

            if (flagged.isNotEmpty) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.red.shade900.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade800),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Flagged Issues',
                        style: TextStyle(
                            color: Colors.redAccent, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    ...flagged.map((f) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 2),
                          child: Row(
                            children: [
                              const Icon(Icons.warning_amber, size: 14, color: Colors.red),
                              const SizedBox(width: 6),
                              Text(f.replaceAll('missing:', 'Missing field: '),
                                  style: const TextStyle(color: Colors.red, fontSize: 13)),
                            ],
                          ),
                        )),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 16),

            // Extracted fields
            const Text('Extracted Fields',
                style: TextStyle(
                    color: Colors.white54,
                    fontSize: 12,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFF161B22),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.white12),
              ),
              child: Column(
                children: [
                  _FieldRow('HS Code', fields['hs_code']),
                  _FieldRow('Invoice Value', fields['invoice_value']),
                  _FieldRow('Container ID', fields['container_id']),
                  _FieldRow('Importer', fields['importer']),
                  _FieldRow('Exporter', fields['exporter']),
                  _FieldRow('Net Weight', fields['net_weight']),
                  _FieldRow('Gross Weight', fields['gross_weight']),
                  _FieldRow('Vessel', fields['vessel_name']),
                  _FieldRow('Port of Origin', fields['port_of_origin'], last: true),
                ],
              ),
            ),

            const SizedBox(height: 24),
            FilledButton(
              onPressed: () =>
                  Navigator.popUntil(context, (r) => r.isFirst),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFF1B4FBF),
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              child: const Text('Back to Home'),
            ),
          ],
        ),
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  final String label;
  final String value;
  final Color colour;

  const _Badge({required this.label, required this.value, required this.colour});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
        decoration: BoxDecoration(
          color: colour.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: colour.withValues(alpha: 0.3)),
        ),
        child: Column(
          children: [
            Text(value,
                style: TextStyle(
                    color: colour,
                    fontWeight: FontWeight.bold,
                    fontSize: 16)),
            const SizedBox(height: 2),
            Text(label,
                style: const TextStyle(color: Colors.white38, fontSize: 11)),
          ],
        ),
      ),
    );
  }
}

class _FieldRow extends StatelessWidget {
  final String label;
  final dynamic value;
  final bool last;

  const _FieldRow(this.label, this.value, {this.last = false});

  @override
  Widget build(BuildContext context) {
    final hasValue = value != null && value.toString().isNotEmpty;
    return Container(
      decoration: BoxDecoration(
        border: last
            ? null
            : const Border(bottom: BorderSide(color: Colors.white12)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          SizedBox(
            width: 110,
            child: Text(label,
                style: const TextStyle(color: Colors.white38, fontSize: 12)),
          ),
          Expanded(
            child: Text(
              hasValue ? value.toString() : '—',
              style: TextStyle(
                  color: hasValue ? Colors.white70 : Colors.white24,
                  fontSize: 13,
                  fontStyle: hasValue ? FontStyle.normal : FontStyle.italic),
            ),
          ),
        ],
      ),
    );
  }
}
