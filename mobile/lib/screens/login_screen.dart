import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/backend_config.dart';
import '../services/operator_service.dart';

class LoginScreen extends StatefulWidget {
  final VoidCallback onLogin;

  const LoginScreen({super.key, required this.onLogin});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _employeeIdCtrl = TextEditingController();
  final _pinCtrl = TextEditingController();
  late final TextEditingController _serverCtrl;
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;
  String? _error;
  bool _obscurePin = true;

  @override
  void initState() {
    super.initState();
    final config = context.read<BackendConfig>();
    _serverCtrl = TextEditingController(text: config.url);
  }

  @override
  void dispose() {
    _employeeIdCtrl.dispose();
    _pinCtrl.dispose();
    _serverCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });

    // Save server URL if changed, capture services before async gap
    final config = context.read<BackendConfig>();
    final operatorService = context.read<OperatorService>();
    final newUrl = _serverCtrl.text.trim();
    if (newUrl.isNotEmpty && newUrl != config.url) {
      await config.setUrl(newUrl);
    }

    final error = await operatorService.login(
      _employeeIdCtrl.text,
      _pinCtrl.text,
    );

    if (!mounted) return;
    if (error == null) {
      widget.onLogin();
    } else {
      setState(() { _loading = false; _error = error; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(32),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Logo
                  const Column(
                    children: [
                      Text('⚡', style: TextStyle(fontSize: 48)),
                      SizedBox(height: 8),
                      Text(
                        'FlashPort',
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                          letterSpacing: -0.5,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'Cikarang Dry Port — Field Scanner',
                        style: TextStyle(color: Colors.white38, fontSize: 13),
                      ),
                    ],
                  ),

                  const SizedBox(height: 48),

                  // Card
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: const Color(0xFF161B22),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white12),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Operator Login',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'Enter your employee ID and PIN',
                          style: TextStyle(color: Colors.white38, fontSize: 13),
                        ),
                        const SizedBox(height: 24),

                        // Employee ID
                        const Text('Employee ID',
                            style: TextStyle(color: Colors.white54, fontSize: 12)),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _employeeIdCtrl,
                          textCapitalization: TextCapitalization.characters,
                          style: const TextStyle(
                            color: Colors.white,
                            fontFamily: 'monospace',
                            letterSpacing: 1.5,
                          ),
                          decoration: _inputDecoration('e.g. CDP-001'),
                          validator: (v) =>
                              (v == null || v.trim().isEmpty) ? 'Required' : null,
                          onFieldSubmitted: (_) => FocusScope.of(context).nextFocus(),
                        ),

                        const SizedBox(height: 16),

                        // PIN
                        const Text('PIN',
                            style: TextStyle(color: Colors.white54, fontSize: 12)),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _pinCtrl,
                          obscureText: _obscurePin,
                          keyboardType: TextInputType.number,
                          style: const TextStyle(color: Colors.white, letterSpacing: 4),
                          decoration: _inputDecoration('••••••').copyWith(
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscurePin ? Icons.visibility_off : Icons.visibility,
                                color: Colors.white38,
                                size: 20,
                              ),
                              onPressed: () =>
                                  setState(() => _obscurePin = !_obscurePin),
                            ),
                          ),
                          validator: (v) =>
                              (v == null || v.trim().isEmpty) ? 'Required' : null,
                          onFieldSubmitted: (_) => _login(),
                        ),

                        const SizedBox(height: 20),
                        const Divider(color: Colors.white12),
                        const SizedBox(height: 12),

                        // Server URL — auto-detected, editable for physical device
                        Row(
                          children: [
                            const Icon(Icons.dns_outlined, size: 14, color: Colors.white24),
                            const SizedBox(width: 6),
                            const Text('Server URL',
                                style: TextStyle(color: Colors.white38, fontSize: 11)),
                          ],
                        ),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _serverCtrl,
                          keyboardType: TextInputType.url,
                          style: const TextStyle(
                              color: Colors.white60,
                              fontSize: 12,
                              fontFamily: 'monospace'),
                          decoration: _inputDecoration('http://localhost:8000').copyWith(
                            contentPadding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 10),
                          ),
                        ),

                        if (_error != null) ...[
                          const SizedBox(height: 14),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 10),
                            decoration: BoxDecoration(
                              color: Colors.red.shade900.withValues(alpha: 0.3),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.red.shade800),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.error_outline,
                                    size: 16, color: Colors.redAccent),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(_error!,
                                      style: const TextStyle(
                                          color: Colors.redAccent, fontSize: 13)),
                                ),
                              ],
                            ),
                          ),
                        ],

                        const SizedBox(height: 24),

                        FilledButton(
                          onPressed: _loading ? null : _login,
                          style: FilledButton.styleFrom(
                            backgroundColor: const Color(0xFF1B4FBF),
                            minimumSize: const Size(double.infinity, 50),
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10)),
                          ),
                          child: _loading
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2, color: Colors.white),
                                )
                              : const Text('Sign In →',
                                  style: TextStyle(
                                      fontSize: 16, fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),
                  const Text(
                    'Contact your supervisor if you forgot your PIN',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white24, fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String hint) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: Colors.white24),
      filled: true,
      fillColor: const Color(0xFF0D1117),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: Colors.white12),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: Colors.white12),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: Color(0xFF1B4FBF)),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: Colors.red.shade700),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: Colors.red.shade700),
      ),
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
    );
  }
}
