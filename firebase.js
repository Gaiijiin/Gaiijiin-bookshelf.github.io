// Импортируем Firebase
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// Конфигурация твоего проекта
const firebaseConfig = {
  apiKey: "AIzaSyAKGLrV5_BpYR2qLIdgauFBsnAXINqWAI4",
  authDomain: "telegbot-8d4cb.firebaseapp.com",
  projectId: "telegbot-8d4cb",
  storageBucket: "telegbot-8d4cb.firebasestorage.app",
  messagingSenderId: "223922614",
  appId: "1:223922614:web:db268f8f579998d4fe5917",
  measurementId: "G-8WL2K05N31"
};

// Инициализация Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

export { db };
