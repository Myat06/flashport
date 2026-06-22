import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:uuid/uuid.dart';
import '../models/scan_record.dart';
import 'preview_screen.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  final _picker = ImagePicker();
  bool _processing = false;
  DocumentType _docType = DocumentType.commercialInvoice;

  Future<void> _capture(ImageSource source) async {
    final file = await _picker.pickImage(
      source: source,
      imageQuality: 95,
      preferredCameraDevice: CameraDevice.rear,
    );
    if (file == null || !mounted) return;
    await _processPath(file.path);
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'],
      withData: false,
    );
    if (result == null || result.files.isEmpty || !mounted) return;
    final path = result.files.single.path;
    if (path == null || !mounted) return;
    await _processPath(path);
  }

  Future<void> _processPath(String filePath) async {
    setState(() => _processing = true);
    try {
      final record = ScanRecord(
        scanId: const Uuid().v4(),
        documentType: _docType,
        imagePath: filePath,
        scannedAt: DateTime.now(),
      );

      if (!mounted) return;
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => PreviewScreen(record: record),
        ),
      );
    } finally {
      if (mounted) setState(() => _processing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('Scan Document'),
      ),
      body: _processing
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Color(0xFF1B4FBF)),
                  SizedBox(height: 16),
                  Text('Processing…', style: TextStyle(color: Colors.white54)),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text('Document Type',
                      style: TextStyle(color: Colors.white54, fontSize: 13)),
                  const SizedBox(height: 8),
                  _DocTypeSelector(
                    selected: _docType,
                    onChanged: (t) => setState(() => _docType = t),
                  ),
                  const SizedBox(height: 32),
                  const Text('Add Document',
                      style: TextStyle(color: Colors.white54, fontSize: 13)),
                  const SizedBox(height: 8),
                  Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF161B22),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.white12),
                    ),
                    child: Column(
                      children: [
                        _CaptureButton(
                          icon: Icons.camera_alt,
                          label: 'Take Photo',
                          subtitle: 'Use camera to photograph document',
                          onTap: () => _capture(ImageSource.camera),
                        ),
                        const Divider(height: 1, color: Colors.white12, indent: 16, endIndent: 16),
                        _CaptureButton(
                          icon: Icons.photo_library,
                          label: 'Upload Photo',
                          subtitle: 'Choose from photo library',
                          onTap: () => _capture(ImageSource.gallery),
                        ),
                        const Divider(height: 1, color: Colors.white12, indent: 16, endIndent: 16),
                        _CaptureButton(
                          icon: Icons.upload_file,
                          label: 'Upload File',
                          subtitle: 'Select a PDF or image from Files',
                          onTap: _pickFile,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  const _OfflineBadge(),
                ],
              ),
            ),
    );
  }
}

class _DocTypeSelector extends StatelessWidget {
  final DocumentType selected;
  final ValueChanged<DocumentType> onChanged;

  const _DocTypeSelector({required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        children: DocumentType.values.map((type) {
          final isSelected = type == selected;
          return ListTile(
            dense: true,
            title: Text(
              type.label,
              style: TextStyle(
                color: isSelected ? const Color(0xFF1B4FBF) : Colors.white70,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
            leading: Icon(
              isSelected ? Icons.radio_button_checked : Icons.radio_button_unchecked,
              color: isSelected ? const Color(0xFF1B4FBF) : Colors.white38,
              size: 20,
            ),
            onTap: () => onChanged(type),
          );
        }).toList(),
      ),
    );
  }
}

class _CaptureButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback onTap;

  const _CaptureButton({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF1B4FBF).withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icon, color: const Color(0xFF1B4FBF), size: 24),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  const SizedBox(height: 2),
                  Text(subtitle,
                      style: const TextStyle(color: Colors.white38, fontSize: 12)),
                ],
              ),
            ),
            const SizedBox(width: 8),
            const Icon(Icons.chevron_right, color: Colors.white24),
          ],
        ),
      ),
    );
  }
}

class _OfflineBadge extends StatelessWidget {
  const _OfflineBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.green.shade900.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.green.shade800),
      ),
      child: const Row(
        children: [
          Icon(Icons.wifi_off, size: 16, color: Colors.green),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              'Works fully offline — syncs automatically when connected',
              style: TextStyle(color: Colors.green, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
