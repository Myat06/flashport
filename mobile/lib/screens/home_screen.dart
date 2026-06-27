import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/scan_record.dart';
import '../services/database_service.dart';
import '../services/operator_service.dart';
import '../services/sync_service.dart';
import 'camera_screen.dart';
import '../widgets/scan_tile.dart';

class HomeScreen extends StatefulWidget {
  final VoidCallback? onLogout;

  const HomeScreen({super.key, this.onLogout});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<ScanRecord> _records = [];
  String _operatorName = '';
  bool _isOnline = true;

  late final Stream<List<ConnectivityResult>> _connectivityStream;

  @override
  void initState() {
    super.initState();
    _load();
    _loadOperatorName();
    context.read<SyncService>().syncCount.addListener(_load);

    _connectivityStream = Connectivity().onConnectivityChanged;
    _connectivityStream.listen((results) {
      final online = results.any((r) => r != ConnectivityResult.none);
      if (mounted) setState(() => _isOnline = online);
      if (online) context.read<SyncService>().syncPending();
    });

    // Check current status once on startup
    Connectivity().checkConnectivity().then((results) {
      if (mounted) {
        setState(() => _isOnline = results.any((r) => r != ConnectivityResult.none));
      }
    });
  }

  @override
  void dispose() {
    context.read<SyncService>().syncCount.removeListener(_load);
    super.dispose();
  }

  Future<void> _load() async {
    final db = context.read<DatabaseService>();
    final records = await db.getAll();
    if (mounted) setState(() => _records = records);
  }

  Future<void> _loadOperatorName() async {
    final name = await context.read<OperatorService>().getName();
    if (mounted) setState(() => _operatorName = name);
  }

  Future<void> _clearData() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('Clear All Data'),
        content: const Text(
          'This will delete all scan records from this device.\n\n'
          'Records already synced to the server are NOT affected.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Clear', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      await context.read<DatabaseService>().clearAll();
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('All local scan records cleared'),
            backgroundColor: Color(0xFF1B4FBF),
          ),
        );
      }
    }
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('Logout'),
        content: const Text('Are you sure you want to log out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Logout', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      await context.read<OperatorService>().logout();
      widget.onLogout?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final pending = _records.where((r) => r.status == SyncStatus.pendingSync).length;

    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Text('⚡', style: TextStyle(fontSize: 18)),
                SizedBox(width: 6),
                Text('FlashPort', style: TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
            if (_operatorName.isNotEmpty)
              Text(
                _operatorName,
                style: const TextStyle(fontSize: 11, color: Colors.white38, fontWeight: FontWeight.normal),
              ),
          ],
        ),
        actions: [
          if (pending > 0)
            Padding(
              padding: const EdgeInsets.only(right: 4),
              child: Chip(
                label: Text('$pending pending'),
                backgroundColor: Colors.orange.shade900,
                labelStyle: const TextStyle(color: Colors.orange, fontSize: 11),
              ),
            ),
          if (_records.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined, size: 22),
              tooltip: 'Clear all data',
              onPressed: _clearData,
            ),
          IconButton(
            icon: const Icon(Icons.logout, size: 22),
            tooltip: 'Logout',
            onPressed: _logout,
          ),
        ],
      ),
      body: Column(
        children: [
          // Offline banner
          if (!_isOnline)
            Container(
              width: double.infinity,
              color: const Color(0xFF7C2D12),
              padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
              child: Row(
                children: [
                  const Icon(Icons.wifi_off, size: 14, color: Colors.orange),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Offline — scans will sync automatically when connected',
                      style: TextStyle(color: Colors.orange, fontSize: 12),
                    ),
                  ),
                  if (_records.any((r) => r.status == SyncStatus.pendingSync))
                    Text(
                      '${_records.where((r) => r.status == SyncStatus.pendingSync).length} queued',
                      style: const TextStyle(color: Colors.orange, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                ],
              ),
            ),

          Expanded(
            child: _records.isEmpty
                ? const _EmptyState()
                : RefreshIndicator(
                    onRefresh: _load,
                    child: ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: _records.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, i) => ScanTile(record: _records[i]),
                    ),
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const CameraScreen()),
          );
          _load();
        },
        icon: const Icon(Icons.document_scanner),
        label: const Text('Scan Document'),
        backgroundColor: const Color(0xFF1B4FBF),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.document_scanner_outlined, size: 72, color: Colors.white24),
          SizedBox(height: 16),
          Text('No scans yet', style: TextStyle(color: Colors.white54, fontSize: 18)),
          SizedBox(height: 8),
          Text('Tap the button below to scan a trade document',
              style: TextStyle(color: Colors.white38, fontSize: 13)),
        ],
      ),
    );
  }
}
