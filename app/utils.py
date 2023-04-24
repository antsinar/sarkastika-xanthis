import requests

from bs4 import BeautifulSoup
from app import CONSTANTS
from app.refine import generate

def fetch_token(url: str) -> dict:
	"""
	Fetches access/session token from webpage's HTML file
	Ever felt this stupid before?
	"""
	req = requests.get(url)
	if req.status_code != 200:
		return {"message": "Site not accessible"}

	soup = BeautifulSoup(req.content, 'html.parser')
	scripts = [x for x in soup.find_all("script") if "const" in x.text]
	
	s = str(scripts[0])
	
	return s[s.index("token"):s.index(';', 188)].replace(' ', '').replace('token', '').replace('=','').replace('\'','')


def match_day(day: str) -> int | str:
	"""
	Matches datetime day string to a valid code
	"""
	code = None

	match day:
		case "Monday":
			code = 1
		case "Tuesday":
			code = 2
		case "Wednesday":
			code = 3
		case "Thursday":
			code = 4
		case "Friday":
			code = 5
		case "Saturday":
			code = 6
		case "Sunday":
			code = 0
		case _:
			code = "error"

	return code


def match_stop(stop: str) -> str | None:
	"""
	matches stop code constants to a readable greek name for ease of use
	"""
	name:str = ""

	match stop:
		case CONSTANTS.MPALTATZI_PROS:
			name = "Μπαλτατζή Μ"
			
		case CONSTANTS.MPALTATZI_APO:
			name = "Μπαλτατζή Ε"
			
		case CONSTANTS.DIMOTIKI_PROS:
			name = "Δημοτική Μ"
			
		case CONSTANTS.TSALDARI_PROS:
			name = "Τσαλδάρη Μ"
			
		case CONSTANTS.KONEL_PROS:
			name = "Κωνσταντίνου & Ελένης Μ"
			
		case CONSTANTS.KONEL_APO:
			name = "Κωνσταντίνου & Ελένης Ε"
			
		case CONSTANTS.TEXN_APO:
			name = "Τεχνική Σχολή (Λέσχη) Ε"
			
		case CONSTANTS.ESTIES_PROS:
			name = "Εστίες Μ"
			
		case CONSTANTS.HMMY_PROS:
			name = "Τμήμα Ηλεκτρολόγων Μηχανικών Μ"
			
		case CONSTANTS.HMMY_APO:
			name = "Τμήμα Ηλεκτρολόγων Μηχανικών Ε"
			
		case CONSTANTS.LEOF_STRATOU_PROS:
			name = "Λεωφόρος Στρατού Μ"

		case CONSTANTS.LEOF_STRATOU_APO:
			name = "Λεωφόρος Στρατού Ε"
			
		case CONSTANTS.POL_PROS:
			name = "Τμήμα Πολιτικών Μηχανικών M"
			
		case CONSTANTS.POL_APO:
			name = "Τμήμα Πολιτικών Μηχανικών E"
			
		case CONSTANTS.ARCH_PROS:
			name = "Τμήμα Αρχιτεκτόνων M"
			
		case CONSTANTS.ARCH_APO:
			name = "Τμήμα Αρχιτεκτόνων Ε"
			
		case CONSTANTS.ENV_PROS:
			name = "Τμήμα Μηχανικών Περιβάλλοντος (Εργαστήρια) Μ"
			
		case CONSTANTS.ENV_APO:
			name = "Τμήμα Μηχανικών Περιβάλλοντος (Εργαστήρια) Ε"
			
		case CONSTANTS.ELENA_APO:
			name = "Ξενοδοχείο Έλενα Ε"
			
		case CONSTANTS.PROKAT:
			name = "Προκάτ (Deprecated) Ε"
			
		case _:
			name = None
			

	return name