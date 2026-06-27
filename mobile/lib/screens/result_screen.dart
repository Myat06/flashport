import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../services/backend_config.dart';

const _apiKey = String.fromEnvironment('API_KEY', defaultValue: 'changeme');

class ResultScreen extends StatefulWidget {
  final Map<String, dynamic> response;

  const ResultScreen({super.key, required this.response});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  Uint8List? _imageBytes;
  int? _imgW;
  int? _imgH;
  List<Map<String, dynamic>> _fullVr = [];
  bool _imageLoading = false;

  @override
  void initState() {
    super.initState();
    _fetchImage();
  }

  Future<void> _fetchImage() async {
    final declarationId = widget.response['declaration_id'] as String?;
    if (declarationId == null) return;

    setState(() => _imageLoading = true);
    try {
      final prefs   = await SharedPreferences.getInstance();
      final baseUrl = prefs.getString('backend_url') ?? BackendConfig.platformDefault;

      final res = await http.get(
        Uri.parse('$baseUrl/declarations/$declarationId/image'),
        headers: {'X-API-Key': _apiKey},
      ).timeout(const Duration(seconds: 30));

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        final b64  = data['image_data'] as String?;
        if (b64 != null && mounted) {
          setState(() {
            _imageBytes = base64Decode(b64);
            _imgW = data['image_width'] as int?;
            _imgH = data['image_height'] as int?;
            _fullVr = (data['validation_results'] as List?)
                    ?.cast<Map<String, dynamic>>() ??
                [];
          });
        }
      }
    } catch (_) {
    } finally {
      if (mounted) setState(() => _imageLoading = false);
    }
  }

  void _openFullScreen() {
    Navigator.push(
      context,
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => _FullDocumentView(
          imageBytes: _imageBytes!,
          imgW: _imgW,
          imgH: _imgH,
          validationResults: _fullVr,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final response = widget.response;

    final confidence = response['confidence_badge'] as String? ?? 'medium';
    final riskScore  = response['risk_score'] as int? ?? 0;
    final riskBadge  = response['risk_badge'] as String? ?? 'yellow';
    final ceisaReady = response['ceisa_ready'] as bool? ?? false;
    final flagged    = (response['flagged_fields'] as List?)?.cast<String>() ?? [];
    final fields     = response['extracted_fields'] as Map<String, dynamic>? ?? {};

    // Prefer fetched full validation results (have bboxes), fall back to sync response
    final rawVr = _fullVr.isNotEmpty
        ? _fullVr
        : ((response['validation_results'] as List?)?.cast<Map<String, dynamic>>() ?? []);
    final vrMap = {
      for (final r in rawVr) r['field_name'] as String: r,
    };

    final (badgeColour, badgeLabel, badgeIcon) = switch (riskBadge) {
      'green' => (Colors.green, 'Low Risk — Green Lane', Icons.check_circle),
      'red'   => (Colors.red, 'High Risk — Red Lane', Icons.warning_rounded),
      _       => (Colors.orange, 'Medium Risk — Yellow Lane', Icons.info_rounded),
    };

    final criticalIssues  = rawVr.where((r) => r['priority'] == 'critical'  && r['is_valid'] == false).length;
    final importantIssues = rawVr.where((r) => r['priority'] == 'important' && r['is_valid'] == false).length;

    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('Scan Result'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Document image ──────────────────────────────────────────────────
            _DocumentImageCard(
              imageBytes: _imageBytes,
              isLoading: _imageLoading,
              onExpand: _imageBytes != null ? _openFullScreen : null,
            ),

            const SizedBox(height: 16),

            // ── Risk summary ────────────────────────────────────────────────────
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
                      style: TextStyle(color: badgeColour, fontSize: 18, fontWeight: FontWeight.bold)),
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

            // ── Badges row ──────────────────────────────────────────────────────
            Row(
              children: [
                _Badge(
                  label: 'OCR Confidence',
                  value: confidence.toUpperCase(),
                  colour: switch (confidence) {
                    'high' => Colors.blue,
                    'low'  => Colors.red,
                    _      => Colors.orange,
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

            // ── Validation pills ────────────────────────────────────────────────
            if (rawVr.isNotEmpty) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  _ValidationPill(
                    label: criticalIssues > 0 ? '$criticalIssues Critical' : '✓ Critical OK',
                    ok: criticalIssues == 0,
                    colour: criticalIssues > 0 ? Colors.red : Colors.green,
                  ),
                  const SizedBox(width: 8),
                  _ValidationPill(
                    label: importantIssues > 0 ? '$importantIssues Important' : '✓ Important OK',
                    ok: importantIssues == 0,
                    colour: importantIssues > 0 ? Colors.orange : Colors.green,
                  ),
                ],
              ),
            ],

            // ── Risk flags ──────────────────────────────────────────────────────
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
                    const Text('Risk Flags',
                        style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    ...flagged.map((f) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 2),
                          child: Row(
                            children: [
                              const Icon(Icons.warning_amber, size: 14, color: Colors.red),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(f.replaceAll('missing:', 'Missing: '),
                                    style: const TextStyle(color: Colors.red, fontSize: 13)),
                              ),
                            ],
                          ),
                        )),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 16),

            // ── Extracted fields ────────────────────────────────────────────────
            const Text('Extracted Fields',
                style: TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFF161B22),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.white12),
              ),
              child: Builder(
                builder: (_) {
                  final entries = fields.entries.toList();
                  if (entries.isEmpty) {
                    return const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No fields extracted', style: TextStyle(color: Colors.white38)),
                    );
                  }
                  return Column(
                    children: [
                      for (int i = 0; i < entries.length; i++)
                        _FieldRow(
                          _fieldLabel(entries[i].key),
                          entries[i].value?.toString(),
                          vrMap[entries[i].key],
                          last: i == entries.length - 1,
                        ),
                    ],
                  );
                },
              ),
            ),

            const SizedBox(height: 24),
            FilledButton(
              onPressed: () => Navigator.popUntil(context, (r) => r.isFirst),
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

// ── Document image card ─────────────────────────────────────────────────────────

class _DocumentImageCard extends StatelessWidget {
  final Uint8List? imageBytes;
  final bool isLoading;
  final VoidCallback? onExpand;

  const _DocumentImageCard({
    required this.imageBytes,
    required this.isLoading,
    this.onExpand,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            const Text('Document Image',
                style: TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold)),
            const Spacer(),
            if (imageBytes != null)
              GestureDetector(
                onTap: onExpand,
                child: const Row(
                  children: [
                    Icon(Icons.open_in_full, size: 14, color: Color(0xFF60a5fa)),
                    SizedBox(width: 4),
                    Text('Full size', style: TextStyle(color: Color(0xFF60a5fa), fontSize: 12)),
                  ],
                ),
              ),
          ],
        ),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: onExpand,
          child: Container(
            height: 180,
            decoration: BoxDecoration(
              color: const Color(0xFF161B22),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.white12),
            ),
            clipBehavior: Clip.antiAlias,
            child: isLoading
                ? const Center(
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Color(0xFF60a5fa),
                    ),
                  )
                : imageBytes != null
                    ? Stack(
                        fit: StackFit.expand,
                        children: [
                          Image.memory(
                            imageBytes!,
                            fit: BoxFit.contain,
                          ),
                          // Tap-to-expand overlay hint
                          Positioned(
                            bottom: 8,
                            right: 8,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.black.withValues(alpha: 0.6),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.zoom_in, size: 12, color: Colors.white70),
                                  SizedBox(width: 4),
                                  Text('Tap to zoom', style: TextStyle(color: Colors.white70, fontSize: 10)),
                                ],
                              ),
                            ),
                          ),
                        ],
                      )
                    : const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.image_not_supported_outlined, color: Colors.white24, size: 36),
                            SizedBox(height: 8),
                            Text('No image available', style: TextStyle(color: Colors.white38, fontSize: 12)),
                          ],
                        ),
                      ),
          ),
        ),
      ],
    );
  }
}

// ── Fullscreen document viewer ──────────────────────────────────────────────────

class _FullDocumentView extends StatefulWidget {
  final Uint8List imageBytes;
  final int? imgW;
  final int? imgH;
  final List<Map<String, dynamic>> validationResults;

  const _FullDocumentView({
    required this.imageBytes,
    this.imgW,
    this.imgH,
    required this.validationResults,
  });

  @override
  State<_FullDocumentView> createState() => _FullDocumentViewState();
}

class _FullDocumentViewState extends State<_FullDocumentView> {
  bool _showOverlay = true;

  @override
  Widget build(BuildContext context) {
    final hasBoxes = widget.validationResults.any((r) => r['bbox'] != null);

    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.black.withValues(alpha: 0.7),
        foregroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Document', style: TextStyle(fontSize: 16)),
        actions: [
          if (hasBoxes)
            TextButton.icon(
              onPressed: () => setState(() => _showOverlay = !_showOverlay),
              icon: Icon(
                _showOverlay ? Icons.visibility_off : Icons.visibility,
                size: 18,
                color: Colors.white70,
              ),
              label: Text(
                _showOverlay ? 'Hide boxes' : 'Show boxes',
                style: const TextStyle(color: Colors.white70, fontSize: 13),
              ),
            ),
        ],
      ),
      body: InteractiveViewer(
        minScale: 0.3,
        maxScale: 6.0,
        child: Center(
          child: widget.imgW != null && widget.imgH != null
              ? AspectRatio(
                  aspectRatio: widget.imgW! / widget.imgH!,
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      return Stack(
                        children: [
                          Image.memory(
                            widget.imageBytes,
                            width: constraints.maxWidth,
                            height: constraints.maxHeight,
                            fit: BoxFit.fill,
                          ),
                          if (_showOverlay && hasBoxes)
                            CustomPaint(
                              size: Size(constraints.maxWidth, constraints.maxHeight),
                              painter: _BboxPainter(
                                validationResults: widget.validationResults,
                                imgW: widget.imgW!,
                                imgH: widget.imgH!,
                              ),
                            ),
                        ],
                      );
                    },
                  ),
                )
              : Image.memory(widget.imageBytes, fit: BoxFit.contain),
        ),
      ),
    );
  }
}

// ── Bounding-box painter ────────────────────────────────────────────────────────

String _fieldLabel(String key) => const {
  'hs_code':       'HS Code',
  'invoice_value': 'Invoice Value',
  'container_id':  'Container ID',
  'importer':      'Importer',
  'exporter':      'Exporter',
  'net_weight':    'Net Weight',
  'gross_weight':  'Gross Weight',
  'invoice_number':'Invoice No.',
  'carton_count':  'Cartons',
  'vessel_name':   'Vessel',
  'port_of_origin':'Port of Origin',
}[key] ?? key;

class _BboxPainter extends CustomPainter {
  final List<Map<String, dynamic>> validationResults;
  final int imgW;
  final int imgH;

  const _BboxPainter({
    required this.validationResults,
    required this.imgW,
    required this.imgH,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final sx = size.width / imgW;
    final sy = size.height / imgH;

    for (final vr in validationResults) {
      final bbox = vr['bbox'] as Map<String, dynamic>?;
      if (bbox == null) continue;

      final x = (bbox['x'] as num).toDouble() * sx;
      final y = (bbox['y'] as num).toDouble() * sy;
      final w = (bbox['w'] as num).toDouble() * sx;
      final h = (bbox['h'] as num).toDouble() * sy;

      final priority = vr['priority'] as String? ?? 'optional';
      final isValid  = vr['is_valid'] as bool? ?? true;

      final Color strokeColor;
      final double strokeWidth;
      if (isValid) {
        strokeColor = const Color(0xFF22c55e);
        strokeWidth = priority == 'critical' ? 3.0 : 2.0;
      } else {
        strokeColor = switch (priority) {
          'critical'  => const Color(0xFFef4444),
          'important' => const Color(0xFFf97316),
          _           => const Color(0xFFeab308),
        };
        strokeWidth = priority == 'critical' ? 3.0 : 2.0;
      }

      // Semi-transparent fill for invalid fields
      if (!isValid) {
        canvas.drawRRect(
          RRect.fromRectAndRadius(Rect.fromLTWH(x, y, w, h), const Radius.circular(3)),
          Paint()
            ..color = strokeColor.withValues(alpha: 0.08)
            ..style = PaintingStyle.fill,
        );
      }

      canvas.drawRRect(
        RRect.fromRectAndRadius(Rect.fromLTWH(x, y, w, h), const Radius.circular(3)),
        Paint()
          ..color = strokeColor
          ..strokeWidth = strokeWidth
          ..style = PaintingStyle.stroke,
      );

      // Field label tag above the box
      final fieldName = vr['field_name'] as String? ?? '';
      final label     = _fieldLabel(fieldName);
      final icon      = isValid ? '✓' : '⚠';
      final tag       = '$icon $label';

      final tp = TextPainter(
        text: TextSpan(
          text: tag,
          style: TextStyle(
            color: Colors.white,
            fontSize: 9 * sx.clamp(0.8, 2.0),
            fontWeight: FontWeight.bold,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();

      const pad = 3.0;
      final tagW = tp.width + pad * 2;
      final tagH = tp.height + pad * 2;
      final tagY = (y - tagH).clamp(0.0, size.height - tagH);

      canvas.drawRRect(
        RRect.fromRectAndRadius(Rect.fromLTWH(x, tagY, tagW, tagH), const Radius.circular(2)),
        Paint()..color = strokeColor,
      );
      tp.paint(canvas, Offset(x + pad, tagY + pad));
    }
  }

  @override
  bool shouldRepaint(covariant _BboxPainter old) =>
      old.validationResults != validationResults ||
      old.imgW != imgW ||
      old.imgH != imgH;
}

// ── Supporting widgets (unchanged) ─────────────────────────────────────────────

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
                style: TextStyle(color: colour, fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(color: Colors.white38, fontSize: 11)),
          ],
        ),
      ),
    );
  }
}

class _ValidationPill extends StatelessWidget {
  final String label;
  final bool ok;
  final Color colour;

  const _ValidationPill({required this.label, required this.ok, required this.colour});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 10),
        decoration: BoxDecoration(
          color: colour.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: colour.withValues(alpha: 0.4)),
        ),
        child: Text(label,
            textAlign: TextAlign.center,
            style: TextStyle(color: colour, fontSize: 11, fontWeight: FontWeight.bold)),
      ),
    );
  }
}

class _FieldRow extends StatelessWidget {
  final String label;
  final dynamic value;
  final Map<String, dynamic>? vr;
  final bool last;

  const _FieldRow(this.label, this.value, this.vr, {this.last = false});

  @override
  Widget build(BuildContext context) {
    final hasValue = value != null && value.toString().isNotEmpty;
    final isValid  = vr?['is_valid'] as bool?;
    final priority = vr?['priority'] as String? ?? 'optional';
    final message  = vr?['message'] as String?;

    Widget? icon;
    Color valueColor = hasValue ? Colors.white70 : Colors.white24;

    if (vr != null) {
      if (isValid == true) {
        icon = const Icon(Icons.check_circle_outline, size: 14, color: Color(0xFF22c55e));
      } else {
        final (iconColor, textColor) = switch (priority) {
          'critical'  => (Colors.red,               Colors.red.shade300),
          'important' => (Colors.orange,             Colors.orange.shade300),
          _           => (Colors.yellow.shade700,    Colors.yellow.shade300),
        };
        icon       = Icon(Icons.warning_amber_rounded, size: 14, color: iconColor);
        valueColor = textColor;
      }
    }

    return Tooltip(
      message: message ?? '',
      child: Container(
        decoration: BoxDecoration(
          border: last ? null : const Border(bottom: BorderSide(color: Colors.white12)),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Row(
          children: [
            if (icon != null) ...[icon, const SizedBox(width: 6)]
            else const SizedBox(width: 20),
            SizedBox(
              width: 100,
              child: Text(label,
                  style: const TextStyle(color: Colors.white38, fontSize: 12)),
            ),
            Expanded(
              child: Text(
                hasValue ? value.toString() : '— missing —',
                style: TextStyle(
                    color: valueColor,
                    fontSize: 13,
                    fontStyle: hasValue ? FontStyle.normal : FontStyle.italic),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
