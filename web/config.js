// Public client configuration.
// These keys are meant to be visible in a web page. Data safety comes from
// Firestore security rules (firestore.rules) and Supabase storage policies,
// and from restricting the Firebase API key to your domains in Google Cloud Console.
window.APP_CONFIG = {
  firebase: {
    apiKey: "AIzaSyCNLIytp9XDkAPbbEJLiDSIK4RxKaEyT_8",
    authDomain: "jkl-trekker.firebaseapp.com",
    projectId: "jkl-trekker",
    storageBucket: "jkl-trekker.firebasestorage.app",
    messagingSenderId: "223565435587",
    appId: "1:223565435587:web:4ffde8a8dec648fc3dc876"
  },
  supabase: {
    url: "https://vxhvcttfzmikxhjtfntd.supabase.co",
    key: "sb_publishable_lMmFY-WQH_78SdZ6-CBlbA_TjDPij8d",
    bucket: "treks"
  },
  // Default map view (centre of J&K + Ladakh)
  mapCenter: [34.1, 76.5],
  mapZoom: 7
};
