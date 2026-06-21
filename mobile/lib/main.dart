import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'firebase_options.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'services/backend_config.dart';
import 'services/database_service.dart';
import 'services/operator_service.dart';
import 'services/sync_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  await FirebaseMessaging.instance.requestPermission();
  FirebaseMessaging.instance.getToken().then((t) {
    if (t != null) debugPrint('FCM token: $t');
  }).catchError((_) {});

  // Load backend URL from SharedPreferences (falls back to platform default)
  final config = BackendConfig();
  await config.load();
  debugPrint('[BackendConfig] url = ${config.url}');

  runApp(FlashPortApp(config: config));
}

class FlashPortApp extends StatefulWidget {
  final BackendConfig config;
  const FlashPortApp({super.key, required this.config});

  @override
  State<FlashPortApp> createState() => _FlashPortAppState();
}

class _FlashPortAppState extends State<FlashPortApp> {
  late final DatabaseService _db;
  late final OperatorService _operator;
  late final SyncService _sync;
  bool? _loggedIn;

  @override
  void initState() {
    super.initState();
    _db = DatabaseService();
    _operator = OperatorService(widget.config);
    _sync = SyncService(_db, _operator, widget.config);
    _listenConnectivity();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final ok = await _operator.isLoggedIn;
    if (mounted) setState(() => _loggedIn = ok);
  }

  void _listenConnectivity() {
    Connectivity().onConnectivityChanged.listen((results) {
      final hasNetwork = results.any((r) => r != ConnectivityResult.none);
      if (hasNetwork) _sync.syncPending();
    });
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<BackendConfig>.value(value: widget.config),
        Provider<DatabaseService>.value(value: _db),
        Provider<OperatorService>.value(value: _operator),
        Provider<SyncService>.value(value: _sync),
      ],
      child: MaterialApp(
        title: 'FlashPort',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF1B4FBF),
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
          scaffoldBackgroundColor: const Color(0xFF0D1117),
          appBarTheme: const AppBarTheme(
            backgroundColor: Color(0xFF161B22),
            foregroundColor: Colors.white,
            elevation: 0,
          ),
        ),
        home: _buildHome(),
      ),
    );
  }

  Widget _buildHome() {
    if (_loggedIn == null) {
      return const Scaffold(
        backgroundColor: Color(0xFF0D1117),
        body: Center(child: CircularProgressIndicator(color: Color(0xFF1B4FBF))),
      );
    }
    if (!_loggedIn!) {
      return LoginScreen(onLogin: () => setState(() => _loggedIn = true));
    }
    return HomeScreen(onLogout: () => setState(() => _loggedIn = false));
  }
}
