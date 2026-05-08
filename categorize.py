RULES = [
    (["MARATHON", "SPEEDWAY", "EXXON", "CHEVRON", "CIRCLE K", "RACETRAC",
      "QT ", "BUC-EE", "BP#", "LOVE'S", "SHELL", "SUNOCO", "MOBIL",
      "VALERO", "PHILLIPS 66", "CASEY'S", "KWIK TRIP", "WAWA"], "Gas"),
    (["MCDONALD", "BURGER KING", "CHICK-FIL", "SUBWAY", "WENDY",
      "TACO BELL", "CHIPOTLE", "DOMINO", "PIZZA HUT", "POPEYES",
      "RAISING CANE", "WHATABURGER", "SONIC ", "PANDA EXPRESS",
      "FIVE GUYS", "IN-N-OUT", "CULVER", "DAIRY QUEEN"], "Fast Food"),
    (["RESTAURANT", "DELI", "SEAFOOD", "GRILL", "KITCHEN", "CAFE",
      "BISTRO", "SUSHI", "STEAKHOUSE", "TST*", "VERTI MARTE",
      "DOORDASH", "GRUBHUB", "UBER EATS", "INSTACART MEALS",
      "JAZZ FEST", "MARY J'S"], "Dining"),
    (["WALMART", "TARGET", "AMAZON", "COSTCO", "KROGER", "PUBLIX",
      "WHOLE FOODS", "TRADER JOE", "ALDI", "SAFEWAY", "HEB ",
      "WINN-DIXIE", "PIGGLY", "FOOD LION"], "Grocery"),
    (["NETFLIX", "SPOTIFY", "HULU", "DISNEY", "APPLE.COM", "APPLE ",
      "GOOGLE ONE", "YOUTUBE", "PEACOCK", "PARAMOUNT", "HBO",
      "AMAZON PRIME", "DROPBOX", "ADOBE"], "Subscriptions"),
    (["CVS", "WALGREENS", "PHARMACY", "MED*", "DOCTOR", "DENTAL",
      "VISION", "HOSPITAL", "CLINIC", "URGENT CARE"], "Health"),
    (["HOTEL", "AIRBNB", "MARRIOTT", "HILTON", "HYATT", "IHG",
      "MOTEL", "HOLIDAY INN", "BEST WESTERN"], "Lodging"),
    (["UBER", "LYFT", "PARKING", "TOLL", "TRANSIT", "METRO ",
      "GREYHOUND", "AMTRAK"], "Transportation"),
    (["DELTA", "UNITED", "AMERICAN AIR", "SOUTHWEST", "SPIRIT AIR",
      "FRONTIER", "JETBLUE"], "Flights"),
    (["TICKETMASTER", "EVENTBRITE", "AMC ", "REGAL ", "CINEMARK",
      "STUBHUB", "LIVE NATION"], "Entertainment"),
    (["AT&T", "VERIZON", "T-MOBILE", "COMCAST", "SPECTRUM",
      "XFINITY", "COX COMM"], "Utilities/Phone"),
    (["PLANET FITNESS", "LA FITNESS", "GOLD'S GYM", "YMCA",
      "EQUINOX", "PELOTON"], "Fitness"),
]


def categorize(description: str) -> str:
    desc = (description or "").upper()
    for keywords, category in RULES:
        if any(kw in desc for kw in keywords):
            return category
    return "Other"
