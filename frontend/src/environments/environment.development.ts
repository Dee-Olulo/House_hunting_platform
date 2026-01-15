export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000',
   paymentConfig: {
    testMode: false,
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