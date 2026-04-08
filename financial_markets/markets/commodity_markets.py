"""
Commodity Markets
=================

Commodity markets facilitate the trading of raw materials and primary
agricultural products. They play a critical role in price discovery for
the global economy and in risk management for producers and consumers.

COMMODITY CLASSIFICATION
────────────────────────

1. ENERGY
   • Crude Oil (WTI, Brent, Dubai/Oman, OPEC Basket)
   • Natural Gas (Henry Hub, TTF, JKM, NBP)
   • Refined Products (Gasoline, Diesel/Gasoil, Jet Fuel, Heating Oil)
   • Coal (Thermal coal, Metallurgical/Coking coal)
   • Electricity (PJM, ERCOT, Nord Pool, EEX)
   • Carbon Credits (EU ETS, California Cap-and-Trade, RGGI)
   • LNG (Liquefied Natural Gas)
   • Ethanol, Biodiesel (Biofuels)
   • Uranium (U3O8)
   • Hydrogen (emerging market)

2. METALS
   Precious Metals:
   • Gold – Safe haven, central bank reserves, jewelry, industrial
   • Silver – Monetary metal + industrial (solar, electronics)
   • Platinum – Automotive catalysts, jewelry, industrial
   • Palladium – Automotive catalysts (gasoline engines)
   • Rhodium – Rarest and most expensive precious metal

   Base / Industrial Metals:
   • Copper – "Dr. Copper" (economic bellwether), electrification demand
   • Aluminum – Lightweight metal, construction, packaging
   • Zinc – Galvanizing steel, batteries
   • Nickel – Stainless steel, EV batteries (key for energy transition)
   • Tin – Solder, electronics
   • Lead – Batteries
   • Iron Ore – Steelmaking (not traded on LME; SGX, DCE)
   • Steel (HRC futures, rebar futures)
   • Cobalt – EV batteries, aerospace
   • Lithium – EV batteries (growing exchange-traded market)

   Minor / Specialty Metals:
   • Rare earth elements, tungsten, molybdenum, vanadium, manganese

3. AGRICULTURE
   Grains & Oilseeds:
   • Corn (Maize) – Largest US crop, feed, ethanol, food
   • Soybeans – Oil, meal (animal feed), biodiesel
   • Wheat – Multiple varieties (SRW, HRW, HRS, Milling)
   • Rice – CBOT rough rice
   • Oats – CBOT
   • Canola (Rapeseed) – ICE Canada, Euronext
   • Palm Oil – Bursa Malaysia, DCE
   • Soybean Oil, Soybean Meal

   Softs (Tropical/Subtropical):
   • Coffee (Arabica – ICE, Robusta – ICE London)
   • Cocoa – ICE, ICE London
   • Sugar (Raw #11, White #5) – ICE
   • Cotton – ICE
   • Rubber – TOCOM, SGX, SHFE
   • Orange Juice – ICE (FCOJ)

   Livestock:
   • Live Cattle – CME
   • Feeder Cattle – CME
   • Lean Hogs – CME

   Dairy:
   • Class III Milk – CME
   • Cheese, Butter, Whey – CME

   Lumber & Forest Products:
   • Random Length Lumber – CME (famously volatile during 2020-2021)

COMMODITY MARKET STRUCTURE
──────────────────────────

Physical vs. Financial Markets:
    Physical: Actual delivery and consumption of commodities
    Financial: Derivatives (futures, options, swaps) for price exposure

Spot / Cash Market:
    Immediate delivery. Prices reflect current supply/demand.
    Physical commodities trade via bilateral contracts, auctions,
    and commodity exchanges.

Futures Market:
    Standardized contracts for future delivery.
    Most positions closed before delivery (offset/rolled).
    Only 1-3% of futures contracts result in physical delivery.

OTC Derivatives:
    Customized bilateral contracts (swaps, forwards, options).
    Large volume in energy and metals.
    Post-Dodd-Frank: many cleared through CCPs and reported to SDRs.

KEY COMMODITY BENCHMARKS
─────────────────────────

Crude Oil:
    • WTI (West Texas Intermediate) – US benchmark, NYMEX/CME, Cushing OK
    • Brent – International benchmark, ICE, North Sea
    • Dubai/Oman – Middle East/Asian benchmark
    • OPEC Reference Basket – Weighted average of OPEC member crudes
    • Pricing: Most global crude priced as differential to Brent

Natural Gas:
    • Henry Hub – US benchmark, NYMEX/CME, Louisiana
    • TTF (Title Transfer Facility) – European benchmark, ICE
    • JKM (Japan Korea Marker) – Asian LNG benchmark, Platts/CME
    • NBP (National Balancing Point) – UK benchmark

Gold:
    • LBMA Gold Price – Twice-daily London fix (AM/PM)
    • COMEX (CME) – Most liquid gold futures
    • Shanghai Gold Exchange – Chinese benchmark

COMMODITY PRICING CONCEPTS
───────────────────────────

Contango vs. Backwardation:
    • Contango: Futures price > Spot price
      Normal for non-perishable commodities (storage costs, financing)
      Creates negative roll yield for long futures positions
    • Backwardation: Futures price < Spot price
      Common during supply shortages
      Creates positive roll yield for long futures positions

Convenience Yield:
    Benefit of holding physical commodity (insurance against shortages).
    Explains why futures can trade below spot (backwardation).
    F = S × e^((r - c + u) × t)
    Where c = convenience yield, u = storage costs, r = risk-free rate

Crack Spread:
    Refining margin: spread between crude oil and refined products.
    3:2:1 crack: 3 barrels crude → 2 barrels gasoline + 1 barrel distillate

Crush Spread:
    Processing margin for soybeans:
    Revenue from soybean meal + soybean oil – cost of soybeans

Spark Spread:
    Power generation margin: electricity price – (natural gas price × heat rate)

Basis:
    Difference between local cash price and benchmark futures price.
    Reflects transportation, quality, and timing differences.

COMMODITY SUPER-CYCLES
───────────────────────
Long-term (10-35 year) periods of above-trend commodity prices driven
by structural demand shifts:
    • 1900s-1920s: Industrialization
    • 1930s-1950s: WWII rearmament and post-war rebuilding
    • 1970s-1980s: Oil shocks, inflation
    • 2000s-2010s: China/EM industrialization
    • 2020s+: Energy transition / "greenflation" debate

KEY COMMODITY MARKET PARTICIPANTS
──────────────────────────────────
• Producers (oil companies, miners, farmers) – Natural sellers/hedgers
• Consumers (airlines, utilities, food companies) – Natural buyers/hedgers
• Physical commodity traders (Vitol, Trafigura, Glencore, Cargill, ADM)
• Speculators and financial investors (hedge funds, CTAs)
• Index investors (commodity index funds, ETFs)
• Central banks (gold reserves)

OPEC AND OPEC+
───────────────
Organization of the Petroleum Exporting Countries:
    • Founded 1960; 13 member countries (2024)
    • Key members: Saudi Arabia, UAE, Iraq, Kuwait, Iran
    • OPEC+ includes Russia, Kazakhstan, and other non-OPEC producers
    • Sets production quotas to influence global oil prices
    • Saudi Arabia is the "swing producer" with significant spare capacity

COMMODITY INDICES
──────────────────
• S&P GSCI (Goldman Sachs Commodity Index) – Energy-heavy (~60%)
• Bloomberg Commodity Index (BCOM) – More diversified, production-weighted
• DBIQ Optimum Yield Diversified Commodity Index
• Rogers International Commodity Index (RICI)
• CRB Index (Thomson Reuters/CoreCommodity)
• S&P GSCI Enhanced Commodity Index
"""
