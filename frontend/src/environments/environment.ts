export const environment = {
  production: true,
  apiUrl: 'http://localhost:5000',
   paymentConfig: {
    testMode: true,
    supportedCurrencies: ['KES', 'USD', 'EUR', 'GBP'],
    defaultCurrency: 'KES',
    mpesa: {
      enabled: true,
      phoneFormat: '254XXXXXXXXX'
    },
    flutterwave: {
      enabled: true
    }
  }
};