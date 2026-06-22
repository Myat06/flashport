import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/scan_record.dart';
import '../services/sync_service.dart';
import 'result_screen.dart';

class PreviewScreen extends StatefulWidget {
  final ScanRecord record;

  const PreviewScreen({super.key, required this.record});

  @override
  State<PreviewScreen> createState() => _PreviewScreenState();
}

class _PreviewScreenState extends State<PreviewScreen>
    with SingleTickerProviderStateMixin {
  bool _saving = false;
  int _uploadStep = 0; // 0=idle 1=preparing 2=uploading 3=processing
  late final AnimationController _pulseCtrl;
  late final Animation<double> _pulse;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
    _pulse = Tween(begin: 0.5, end: 1.0).animate(_pulseCtrl);
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    super.dispose();
  }

  Future<void> _confirm() async {
    setState(() { _saving = true; _uploadStep = 1; });

    await Future.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;
    setState(() => _uploadStep = 2);

    try {
      final sync = context.read<SyncService>();

      // Switch to step 3 after a short delay so user sees "uploading"
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted && _saving) setState(() => _uploadStep = 3);
      });

      final serverResponse = await sync.syncOneNow(widget.record);

      if (!mounted) return;

      if (serverResponse != null) {
        await Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => ResultScreen(response: serverResponse)),
        );
      } else {
        final url = context.read<SyncService>().configUrl;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Saved as pending — server: $url'),
            backgroundColor: Colors.orange.shade800,
            duration: const Duration(seconds: 6),
          ),
        );
        Navigator.popUntil(context, (r) => r.isFirst);
      }
    } finally {
      if (mounted) setState(() { _saving = false; _uploadStep = 0; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isPdf = widget.record.imagePath.toLowerCase().endsWith('.pdf');
    final file = File(widget.record.imagePath);
    final fileSizeKb = file.existsSync()
        ? (file.lengthSync() / 1024).toStringAsFixed(0)
        : '—';
    final fileName = widget.record.imagePath.split('/').last;

    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: Text('Review — ${widget.record.documentType.label}'),
      ),
      body: _saving ? _UploadingView(step: _uploadStep, pulse: _pulse) : _PreviewBody(
        record: widget.record,
        isPdf: isPdf,
        fileName: fileName,
        fileSizeKb: fileSizeKb,
      ),
      bottomNavigationBar: _saving ? null : SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.refresh, size: 18),
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
                  onPressed: _confirm,
                  icon: const Icon(Icons.cloud_upload_rounded, size: 20),
                  label: const Text('Upload & Sync',
                      style: TextStyle(fontWeight: FontWeight.bold)),
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

// ── Preview body — shown before upload ──────────────────────────────────────
class _PreviewBody extends StatelessWidget {
  final ScanRecord record;
  final bool isPdf;
  final String fileName;
  final String fileSizeKb;

  const _PreviewBody({
    required this.record,
    required this.isPdf,
    required this.fileName,
    required this.fileSizeKb,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Document preview with "attached" badge
          Stack(
            children: [
              if (!isPdf && record.imagePath.isNotEmpty)
                Container(
                  height: 260,
                  width: double.infinity,
                  color: Colors.black,
                  child: Image.file(
                    File(record.imagePath),
                    fit: BoxFit.contain,
                  ),
                )
              else
                Container(
                  height: 160,
                  width: double.infinity,
                  color: const Color(0xFF161B22),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1B4FBF).withValues(alpha: 0.15),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.picture_as_pdf,
                            size: 52, color: Color(0xFF1B4FBF)),
                      ),
                      const SizedBox(height: 10),
                      const Text('PDF Document',
                          style: TextStyle(color: Colors.white54, fontSize: 13)),
                    ],
                  ),
                ),

              // Green "attached" badge top-right
              Positioned(
                top: 12,
                right: 12,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: Colors.green.shade800,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                          color: Colors.black.withValues(alpha: 0.4),
                          blurRadius: 6)
                    ],
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check_circle, size: 14, color: Colors.white),
                      SizedBox(width: 5),
                      Text('Attached',
                          style: TextStyle(
                              color: Colors.white,
                              fontSize: 11,
                              fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
              ),
            ],
          ),

          // File info strip
          Container(
            color: const Color(0xFF161B22),
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                Icon(
                  isPdf ? Icons.picture_as_pdf : Icons.image_rounded,
                  size: 16,
                  color: Colors.white38,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    fileName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style:
                        const TextStyle(color: Colors.white54, fontSize: 11),
                  ),
                ),
                Text(
                  '$fileSizeKb KB',
                  style:
                      const TextStyle(color: Colors.white38, fontSize: 11),
                ),
              ],
            ),
          ),

          const Divider(height: 1, color: Colors.white12),

          // Details
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _InfoRow(
                    label: 'Document Type',
                    value: record.documentType.label),
                const SizedBox(height: 10),
                _InfoRow(
                    label: 'Scanned At',
                    value: record.scannedAt
                        .toLocal()
                        .toString()
                        .substring(0, 16)),
                const SizedBox(height: 20),

                // Ready to upload card
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.green.shade900.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                        color: Colors.green.shade800.withValues(alpha: 0.5)),
                  ),
                  child: const Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.check_circle_outline,
                          size: 18, color: Colors.green),
                      SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Document ready to upload',
                                style: TextStyle(
                                    color: Colors.green,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12)),
                            SizedBox(height: 4),
                            Text(
                              'Tap Upload & Sync to send to server for OCR '
                              'processing and risk analysis. If offline, it '
                              'will sync automatically when connected.',
                              style: TextStyle(
                                  color: Colors.green, fontSize: 11, height: 1.5),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Upload progress view — shown while syncing ───────────────────────────────
class _UploadingView extends StatelessWidget {
  final int step;
  final Animation<double> pulse;

  static const _steps = [
    (Icons.compress,         'Preparing document...'),
    (Icons.cloud_upload,     'Uploading to server...'),
    (Icons.psychology_rounded,'Running OCR & AI analysis...'),
  ];

  const _UploadingView({required this.step, required this.pulse});

  @override
  Widget build(BuildContext context) {
    final activeStep = (step - 1).clamp(0, _steps.length - 1);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Pulsing upload icon
            FadeTransition(
              opacity: pulse,
              child: Container(
                width: 90,
                height: 90,
                decoration: BoxDecoration(
                  color: const Color(0xFF1B4FBF).withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                  border: Border.all(
                      color: const Color(0xFF1B4FBF).withValues(alpha: 0.4),
                      width: 2),
                ),
                child: const Icon(Icons.cloud_upload_rounded,
                    size: 42, color: Color(0xFF1B4FBF)),
              ),
            ),

            const SizedBox(height: 32),

            // Step indicators
            ..._steps.asMap().entries.map((e) {
              final i = e.key;
              final (icon, label) = e.value;
              final isDone = i < activeStep;
              final isActive = i == activeStep;
              final _ = i > activeStep; // pending — used for styling via isDone/isActive

              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  children: [
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isDone
                            ? Colors.green.shade700
                            : isActive
                                ? const Color(0xFF1B4FBF)
                                : Colors.white12,
                      ),
                      child: Center(
                        child: isDone
                            ? const Icon(Icons.check, size: 16,
                                color: Colors.white)
                            : isActive
                                ? SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white.withValues(alpha: 0.9)),
                                  )
                                : Icon(icon, size: 16, color: Colors.white24),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      label,
                      style: TextStyle(
                        fontSize: 13,
                        color: isDone
                            ? Colors.green
                            : isActive
                                ? Colors.white
                                : Colors.white24,
                        fontWeight: isActive
                            ? FontWeight.bold
                            : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              );
            }),

            const SizedBox(height: 32),
            Text(
              'Please keep the app open...',
              style: TextStyle(
                  color: Colors.white38, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 110,
          child: Text(label,
              style: const TextStyle(color: Colors.white38, fontSize: 12)),
        ),
        Expanded(
          child: Text(value,
              style: const TextStyle(color: Colors.white70, fontSize: 13)),
        ),
      ],
    );
  }
}
