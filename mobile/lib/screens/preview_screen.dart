import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/scan_record.dart';
import '../services/sync_service.dart';
import 'result_screen.dart';

class PreviewScreen extends StatefulWidget {
  final ScanRecord record;
  final Map<String, dynamic>? ocrPreview;

  const PreviewScreen({super.key, required this.record, this.ocrPreview});

  @override
  State<PreviewScreen> createState() => _PreviewScreenState();
}

class _PreviewScreenState extends State<PreviewScreen> {
  bool _saving = false;

  Future<void> _confirm() async {
    setState(() => _saving = true);
    try {
      final sync = context.read<SyncService>();
      final serverResponse = await sync.syncOneNow(widget.record);

      if (!mounted) return;

      if (serverResponse != null) {
        await Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => ResultScreen(response: serverResponse)),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Saved — will sync automatically when online'),
            backgroundColor: Color(0xFF1B4FBF),
          ),
        );
        Navigator.popUntil(context, (r) => r.isFirst);
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isPdf = widget.record.imagePath.toLowerCase().endsWith('.pdf');
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: Text('OCR Preview — ${widget.record.documentType.label}'),
      ),
      body: Column(
        children: [
          // Document image or PDF placeholder
          if (!isPdf && widget.record.imagePath.isNotEmpty)
            Container(
              height: 240,
              width: double.infinity,
              color: Colors.black,
              child: Image.file(File(widget.record.imagePath), fit: BoxFit.contain),
            )
          else
            Container(
              height: 120,
              width: double.infinity,
              color: Colors.black,
              child: const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.picture_as_pdf, size: 48, color: Colors.white24),
                    SizedBox(height: 6),
                    Text('PDF Document', style: TextStyle(color: Colors.white38, fontSize: 13)),
                  ],
                ),
              ),
            ),

          // OCR result or offline notice
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: widget.ocrPreview != null
                  ? _OcrResultSection(preview: widget.ocrPreview!)
                  : const _OfflineNotice(),
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _saving ? null : () => Navigator.pop(context),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retake'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.white54,
                    side: const BorderSide(color: Colors.white24),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: FilledButton.icon(
                  onPressed: _saving ? null : _confirm,
                  icon: _saving
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.check_circle),
                  label: Text(_saving ? 'Saving…' : 'Confirm & Save'),
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF1B4FBF),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OcrResultSection extends StatelessWidget {
  final Map<String, dynamic> preview;

  const _OcrResultSection({required this.preview});

  @override
  Widget build(BuildContext context) {
    final confidence = preview['confidence_badge'] as String? ?? 'medium';
    final riskScore = preview['risk_score'] as int? ?? 0;
    final riskBadge = preview['risk_badge'] as String? ?? 'yellow';
    final flagged = (preview['flagged_fields'] as List?)?.cast<String>() ?? [];
    final fields = preview['extracted_fields'] as Map<String, dynamic>? ?? {};

    final riskColor = switch (riskBadge) {
      'green' => Colors.green,
      'red' => Colors.red,
      _ => Colors.orange,
    };
    final confidenceColor = switch (confidence) {
      'high' => Colors.blue,
      'low' => Colors.red,
      _ => Colors.orange,
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            _Badge(label: 'OCR Confidence', value: confidence.toUpperCase(), colour: confidenceColor),
            const SizedBox(width: 12),
            _Badge(label: 'Risk Score', value: '$riskScore%', colour: riskColor),
          ],
        ),

        if (flagged.isNotEmpty) ...[
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.red.shade900.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.red.shade800),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.warning_amber, size: 14, color: Colors.redAccent),
                    SizedBox(width: 6),
                    Text('Flagged Issues',
                        style: TextStyle(
                            color: Colors.redAccent,
                            fontWeight: FontWeight.bold,
                            fontSize: 13)),
                  ],
                ),
                const SizedBox(height: 6),
                ...flagged.map((f) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Text(
                        f.replaceAll('missing:', 'Missing: '),
                        style: const TextStyle(color: Colors.red, fontSize: 12),
                      ),
                    )),
              ],
            ),
          ),
        ],

        const SizedBox(height: 16),
        const Text('Extracted Fields',
            style: TextStyle(
                color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold)),
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

        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF161B22),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.white12),
          ),
          child: const Row(
            children: [
              Icon(Icons.info_outline, size: 14, color: Colors.white38),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Review the fields above. Tap Confirm & Save to submit.',
                  style: TextStyle(color: Colors.white38, fontSize: 12, height: 1.4),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _OfflineNotice extends StatelessWidget {
  const _OfflineNotice();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white12),
      ),
      child: const Row(
        children: [
          Icon(Icons.wifi_off, size: 18, color: Colors.white38),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'OCR preview unavailable — device is offline.\nTesseract will process the document automatically when connected.',
              style: TextStyle(color: Colors.white38, fontSize: 13, height: 1.5),
            ),
          ),
        ],
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
                    color: colour, fontWeight: FontWeight.bold, fontSize: 16)),
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
        border: last ? null : const Border(bottom: BorderSide(color: Colors.white12)),
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
                fontStyle: hasValue ? FontStyle.normal : FontStyle.italic,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
