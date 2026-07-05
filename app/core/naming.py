"""Newborn name suggestions from the Moon nakshatra pada.

Classical Vedic naming: the first syllable of the child's name is chosen
from the syllable assigned to the janma-nakshatra pada. Includes Odia name
examples for each syllable.
"""
from __future__ import annotations

# 27 nakshatras x 4 padas -> starting syllables (standard table)
PADA_SYLLABLES = [
    ["Chu", "Che", "Cho", "La"], ["Li", "Lu", "Le", "Lo"],
    ["A", "I", "U", "E"], ["O", "Va", "Vi", "Vu"],
    ["Ve", "Vo", "Ka", "Ki"], ["Ku", "Gha", "Nga", "Chha"],
    ["Ke", "Ko", "Ha", "Hi"], ["Hu", "He", "Ho", "Da"],
    ["Di", "Du", "De", "Do"], ["Ma", "Mi", "Mu", "Me"],
    ["Mo", "Ta", "Ti", "Tu"], ["Te", "To", "Pa", "Pi"],
    ["Pu", "Sha", "Na", "Tha"], ["Pe", "Po", "Ra", "Ri"],
    ["Ru", "Re", "Ro", "Ta"], ["Ti", "Tu", "Te", "To"],
    ["Na", "Ni", "Nu", "Ne"], ["No", "Ya", "Yi", "Yu"],
    ["Ye", "Yo", "Bha", "Bhi"], ["Bhu", "Dha", "Pha", "Dha"],
    ["Bhe", "Bho", "Ja", "Ji"], ["Khi", "Khu", "Khe", "Kho"],
    ["Ga", "Gi", "Gu", "Ge"], ["Go", "Sa", "Si", "Su"],
    ["Se", "So", "Da", "Di"], ["Du", "Tha", "Jha", "Na"],
    ["De", "Do", "Cha", "Chi"],
]

# A few Odia-flavoured example names per common starting syllable.
NAME_BANK = {
    "A": (["Abhinab", "Amiya", "Anshuman", "Arka", "Ananta"],
          ["Ananya", "Arpita", "Amrita", "Aparajita", "Annapurna"]),
    "Chu": (["Chudamani"], ["Chumki"]),
    "Che": (["Chetan"], ["Chetana"]),
    "Cho": (["Chittaranjan"], ["Chhabirani"]),
    "La": (["Lalit", "Laxman", "Laxmidhar"], ["Lalita", "Laxmipriya"]),
    "Li": (["Lingaraj"], ["Lipsa", "Lily"]),
    "Lu": (["Lucky"], ["Luna"]),
    "Le": (["Lekhraj"], ["Leena"]),
    "Lo": (["Lokanath", "Lochan"], ["Lopamudra"]),
    "I": (["Indramani", "Ishan"], ["Ipsita", "Indira", "Itishree"]),
    "U": (["Umakanta", "Umesh", "Uttam"], ["Urmila", "Usharani"]),
    "E": (["Ekalabya", "Eshan"], ["Ela", "Eshita"]),
    "O": (["Omkar", "Omprakash"], ["Oisharya"]),
    "Va": (["Vasant", "Banamali", "Basudev"], ["Vasudha", "Banalata"]),
    "Vi": (["Vijay", "Bibhuti", "Biswajit"], ["Vidya", "Bidyutlata"]),
    "Ka": (["Kartik", "Kalandi", "Kanhu"], ["Kabita", "Kalpana", "Kanaklata"]),
    "Ki": (["Kishore", "Kirtan"], ["Kiran", "Kinjal"]),
    "Ku": (["Kulamani", "Kunal"], ["Kumudini", "Kuni"]),
    "Ke": (["Kedar", "Keshab"], ["Ketaki"]),
    "Ko": (["Koushik"], ["Koel", "Komal"]),
    "Ha": (["Harihar", "Harekrushna", "Hemanta"], ["Haripriya", "Hemalata"]),
    "Hi": (["Himanshu", "Hitesh"], ["Hiranmayee", "Hina"]),
    "Hu": (["Hrushikesh"], ["Husnara"]),
    "He": (["Hemant", "Hemendra"], ["Hema", "Hemalata"]),
    "Ho": (["Hrudananda"], ["Holika"]),
    "Da": (["Dasarathi", "Debendra", "Dayanidhi"], ["Damayanti", "Debaki"]),
    "Di": (["Dibakar", "Dilip", "Dinabandhu"], ["Dipti", "Dibyajyoti"]),
    "Du": (["Durgamadhab", "Duryodhan"], ["Durga", "Dukhi"]),
    "De": (["Debasish", "Debraj"], ["Debasmita", "Devi"]),
    "Do": (["Dolagobinda"], ["Dolly"]),
    "Ma": (["Madhusudan", "Manoj", "Mahesh"], ["Mamata", "Madhusmita", "Manasi"]),
    "Mi": (["Mihir", "Milan"], ["Mitali", "Minati"]),
    "Mu": (["Muralidhar", "Mukesh"], ["Mukta", "Mumtaz"]),
    "Me": (["Meghanad"], ["Meghana", "Menaka"]),
    "Mo": (["Mohan", "Monoranjan"], ["Monalisa", "Mousumi"]),
    "Ta": (["Tapan", "Tarini", "Trilochan"], ["Tapaswini", "Tanuja"]),
    "Ti": (["Tikeswar"], ["Tilottama"]),
    "Tu": (["Tusar"], ["Tulasi"]),
    "Te": (["Tejaswi"], ["Tejaswini"]),
    "To": (["Tofan"], ["Tosha"]),
    "Pa": (["Pabitra", "Prasanna", "Padmalochan"], ["Padmini", "Pallabi"]),
    "Pi": (["Pitambar", "Pinaki"], ["Pinky", "Piyali"]),
    "Pu": (["Purnachandra", "Purusottam"], ["Pujarani", "Punyatoya"]),
    "Pe": (["Prem"], ["Prema"]),
    "Po": (["Poshak"], ["Pousali"]),
    "Sha": (["Shankar", "Sharat"], ["Sharmila", "Shanti"]),
    "Na": (["Narayan", "Nabakishore", "Nrusingha"], ["Nandita", "Nalini", "Namita"]),
    "Tha": (["Thakur"], ["Thakurani"]),
    "Ra": (["Raghunath", "Rabindra", "Ramesh"], ["Rashmita", "Ranjita"]),
    "Ri": (["Rituraj"], ["Riya", "Ritika"]),
    "Ru": (["Rudra", "Rupak"], ["Rukmini", "Rupali"]),
    "Re": (["Rebati"], ["Reena", "Rekha"]),
    "Ro": (["Rohit", "Roshan"], ["Rojalin", "Roshni"]),
    "Ni": (["Nilamani", "Niranjan", "Nirmal"], ["Nibedita", "Nirupama"]),
    "Nu": (["Nrupesh"], ["Nutan"]),
    "Ne": (["Netrananda"], ["Neha", "Nehal"]),
    "No": (["Nolin"], ["Nomita"]),
    "Ya": (["Yashobanta", "Yudhisthir"], ["Yashoda", "Yamini"]),
    "Yi": (["Yindra"], ["Yina"]),
    "Yu": (["Yugal", "Yuvraj"], ["Yukta"]),
    "Ye": (["Yeshwant"], ["Yesha"]),
    "Yo": (["Yogesh", "Yogendra"], ["Yogita", "Yogamaya"]),
    "Bha": (["Bhagaban", "Bhaskar", "Bhabani"], ["Bhagyalaxmi", "Bharati"]),
    "Bhi": (["Bhima", "Bhikari"], ["Bhismita"]),
    "Bhu": (["Bhubaneswar", "Bhupendra"], ["Bhumika"]),
    "Bhe": (["Bhera"], ["Bhena"]),
    "Bho": (["Bholanath"], ["Bhoomika"]),
    "Dha": (["Dhaneswar", "Dhruba"], ["Dhanalaxmi", "Dhara"]),
    "Pha": (["Phani", "Phakir"], ["Phulmani"]),
    "Ja": (["Jagannath", "Jagadish", "Janardan"], ["Jayanti", "Jagyaseni"]),
    "Ji": (["Jitendra", "Jibanananda"], ["Jinali"]),
    "Jha": (["Jhadeswar"], ["Jharana"]),
    "Khi": (["Khirod"], ["Khirabdhi"]),
    "Khu": (["Khusiram"], ["Khusi"]),
    "Khe": (["Khetrabasi"], ["Kheerabala"]),
    "Kho": (["Khokan"], ["Khoina"]),
    "Ga": (["Ganeswar", "Gangadhar", "Gopal"], ["Gayatri", "Gitanjali"]),
    "Gi": (["Girish", "Girija"], ["Gitika"]),
    "Gu": (["Gurucharan", "Gunanidhi"], ["Gunjan"]),
    "Ge": (["Geetesh"], ["Geeta"]),
    "Go": (["Gobinda", "Gourahari", "Gopinath"], ["Gouri", "Golap"]),
    "Sa": (["Sarat", "Satyabrata", "Sanatan"], ["Sasmita", "Sabitri", "Sanjukta"]),
    "Si": (["Simanchal", "Siddharth"], ["Sipra", "Sisirkana"]),
    "Su": (["Sudhir", "Surendra", "Subash"], ["Sujata", "Susama", "Subhashree"]),
    "Se": (["Sebak"], ["Sephali", "Selina"]),
    "So": (["Somanath", "Soumya"], ["Somalin", "Sonali"]),
    "Cha": (["Chandan", "Chakradhar"], ["Champa", "Chandini"]),
    "Chi": (["Chinmaya", "Chittaranjan"], ["Chinmayee", "Chitralekha"]),
    "Chha": (["Chhabindra"], ["Chhaya"]),
    "Gha": (["Ghanashyam"], ["Ghungur"]),
    "Nga": (["Nagarjun"], ["Nagalaxmi"]),
    "Ve": (["Benudhar", "Bedabyasa"], ["Bela", "Benulata"]),
    "Vo": (["Bansidhar"], ["Bonita"]),
    "Vu": (["Bulu"], ["Bulbul"]),
}

RASHI_LUCKY = [
    {"gem": "Red Coral", "deity": "Hanuman/Kartikeya", "day": "Tuesday"},
    {"gem": "Diamond/Opal", "deity": "Lakshmi", "day": "Friday"},
    {"gem": "Emerald", "deity": "Vishnu", "day": "Wednesday"},
    {"gem": "Pearl", "deity": "Shiva/Parvati", "day": "Monday"},
    {"gem": "Ruby", "deity": "Surya", "day": "Sunday"},
    {"gem": "Emerald", "deity": "Vishnu", "day": "Wednesday"},
    {"gem": "Diamond/Opal", "deity": "Lakshmi", "day": "Friday"},
    {"gem": "Red Coral", "deity": "Hanuman", "day": "Tuesday"},
    {"gem": "Yellow Sapphire", "deity": "Jagannath/Vishnu", "day": "Thursday"},
    {"gem": "Blue Sapphire", "deity": "Shani/Shiva", "day": "Saturday"},
    {"gem": "Blue Sapphire", "deity": "Shani/Shiva", "day": "Saturday"},
    {"gem": "Yellow Sapphire", "deity": "Jagannath/Vishnu", "day": "Thursday"},
]


def suggest_names(nak_index: int, pada: int, gender: str = "any") -> dict:
    syllable = PADA_SYLLABLES[nak_index][max(1, min(4, pada)) - 1]
    boys, girls = NAME_BANK.get(syllable, ([], []))
    out = {
        "syllable": syllable,
        "all_pada_syllables": PADA_SYLLABLES[nak_index],
        "note": ("Traditional Vedic naming: the name should begin with the "
                 f"syllable '{syllable}' for this janma-nakshatra pada."),
    }
    if gender in ("male", "any"):
        out["boy_names"] = boys
    if gender in ("female", "any"):
        out["girl_names"] = girls
    return out
