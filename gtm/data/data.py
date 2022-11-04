class Data:

    # pairs of candles
    poc = {}
    

    # pairs of orderbook
    pod = {}

    # pairs of diff orderbook

    podo = {}

    # signals

    signals = {}

    # coin list inside of spot
    spot = {}

    # trade history
    th = {}

    # Database Manager
    db = None

    # Binance Manager
    bm = None

    # Logger list
    logger = {}

    # notification Handler
    nh = None

    # TOTAL VALUE OF SPOT
    sow = 0


    # CONSTANTS
    WALL_SENSIVITY = 0.05