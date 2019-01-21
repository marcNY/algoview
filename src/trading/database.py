

TV_to_IB = {'EURUSD': {'symbol': 'EUR', 'secType': 'CASH', 'currency': 'USD', 'exchange': 'IDEALPRO',
                       'expiry': None},
            'ES1!, 1': {'symbol': 'ES', 'secType': 'FUT', 'currency': 'USD', 'exchange': 'GLOBEX',
                        'expiry': '201903'},
            'SPY': {'symbol': 'SPY', 'secType': 'STK', 'currency': 'USD', 'exchange': 'ARCA',
                    'expiry': None},
            'CL1!, 1': {'symbol': 'CL', 'secType': 'FUT', 'currency': 'USD', 'exchange': 'NYMEX',
                        'expiry': '201902'},
            'USO': {'symbol': 'USO', 'secType': 'STK', 'currency': 'USD', 'exchange': 'BATS',
                    'expiry': None},
            'GC1!, 1': {'symbol': 'GC', 'secType': 'FUT', 'currency': 'USD', 'exchange': 'NYMEX',
                        'expiry': '201902'},
            'GLD': {'symbol': 'GLD', 'secType': 'STK', 'currency': 'USD', 'exchange': 'ARCA',
                    'expiry': None},
            'TY1!, 1': {'symbol': 'ZN', 'secType': 'FUT', 'currency': 'USD', 'exchange': 'ECBOT',
                        'expiry': '201903'},
            'IBKR': {'symbol': 'IBKR', 'secType': 'STK', 'currency': 'USD', 'exchange': 'ISLAND',
                     'expiry': None},
            'XLV': {'symbol': 'XLV', 'secType': 'STK', 'currency': 'USD', 'exchange': 'ISLAND',
                    'expiry': None},
            }

conId_to_ul = {12087792: 'EURUSD',
               756733: 'SPY',
               38590758: 'USO',
               51529211: 'GLD',
               4215205: 'XLV',
               43645865: 'IBKR',
              }

bar_to_mins = {'1d': 1440, '4h': 240, '1h': 60, '30m': 30, '15m': 15, '5m': 5, '1m': 1}
bar_to_str = {'1d': '1 day', '4h': '4 hours', '1h': '30 mins', '30m': '30 mins', '15m': '15 mins', '5m': '5 mins', '1m': '1 min'}