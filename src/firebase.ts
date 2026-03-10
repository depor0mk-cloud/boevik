import admin from 'firebase-admin';
import dotenv from 'dotenv';

dotenv.config();

const getServiceAccount = () => {
  const privateKey = process.env.FIREBASE_PRIVATE_KEY;
  const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;
  const projectId = process.env.FIREBASE_PROJECT_ID;

  if (privateKey && clientEmail && projectId) {
    return {
      projectId,
      clientEmail,
      privateKey: privateKey.replace(/\\n/g, '\n'),
    };
  }

  console.error('Firebase credentials missing. Please set FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, and FIREBASE_PRIVATE_KEY in environment variables.');
  throw new Error('Firebase credentials not configured.');
};

const serviceAccount = getServiceAccount();

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: process.env.FIREBASE_DATABASE_URL
});

export const db = admin.database();

export const getSettings = async () => {
  const ref = db.ref('settings');
  const snapshot = await ref.once('value');
  let settings = snapshot.val();
  
  if (!settings) {
    settings = {
      bot_disabled: false,
      test_mode: false,
      sleep_mode: null,
      prices: {
        factory_finance: 1000,
        factory_weapon: 1250,
        production_create: 1000,
        production_upgrade: 1000
      },
      clan_limit: 15
    };
    await ref.set(settings);
  }
  return settings;
};

export const updateSettings = async (data: any) => {
  await db.ref('settings').update(data);
};
