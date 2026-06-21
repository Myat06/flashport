import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) throw UnsupportedError('Web is not supported.');
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyDC2b3lZTEK_wv4TsLan4j4yZoq_q6JIAQ',
    appId: '1:192427322003:android:a36f29765c39f6562afb66',
    messagingSenderId: '192427322003',
    projectId: 'flashport-9870d',
    storageBucket: 'flashport-9870d.firebasestorage.app',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyA5XiM1--kiBVCHqOVg8nOyZSd7drpGDM8',
    appId: '1:192427322003:ios:f84e86da807d56f62afb66',
    messagingSenderId: '192427322003',
    projectId: 'flashport-9870d',
    storageBucket: 'flashport-9870d.firebasestorage.app',
    iosBundleId: 'com.flashport.mobile',
  );
}
