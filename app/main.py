import requests
import ast
import json

from datetime import datetime, timezone
import time
from os import path
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from app import CONSTANTS
from app.utils import fetch_token, match_stop, match_day
from app.refine import generate, refresh


app = FastAPI()


origins = [
    "http://localhost",
    "http://localhost:8000", # change port for your frontend framework
    CONSTANTS.API_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get_root(bgTask: BackgroundTasks):
	today = datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%A-%d-%m-%Y")

	if not path.isfile(f"./app/logs/{today}.json"):
		bgTask.add_task(generate)

	refresh_times = [
		"5:55",
		"9:55",
		"13:55",
		"17:55",
	]

	if datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%H:%M") in refresh_times:
		bgTask.add_task(refresh)

	return {
		"available_routes": [
				"GET /help/info",
				"GET /help/codes/days",
				"GET /help/codes/stops",
				"GET /route/{stop_id}/{day_id}",
				"GET /next/{stop_id}",
				"POST /generate"
			]
	}


@app.get("/help/info")
async def get_help_info():
	now = datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%A %d %m %Y - %H:%M:%S")
	return {
		"date": now,
		"description": "This is an open version of citybus' REST API, used by busses in many cities, including Xanthi. Currenty it only shows the timetable of the 07 line in Xanthi, which includes the Techical University Faculties sited outside the city. Feel free to modify for your city or your route.",
		"about": "This will stay up and running until the developers remove that otherwise pointless session token from their html page. Why do you need one anyway if its open for everyone to see?",
		"today's_message": "Living in 2023: Δίνουμε 1,20 για να κάνουμε πάνω κάτω ένα παράνομο δρόμο εκτός αστικού ιστού.",
		"prompt": "Μη στηρίζετε με κανένα τρόπο τα αστικά Ξάνθης."
	}


@app.get("/help/codes/days")
async def get_help_codes_days():
	return  {
		"DAY CODES": [
			{"Δευτέρα": CONSTANTS.MON},
			{"Τρίτη": CONSTANTS.TUE},
			{"Τετάρτη": CONSTANTS.WED},
			{"Πέμπτη": CONSTANTS.THU},
			{"Παρασκευή": CONSTANTS.FRI},
			{"Σάββατο": CONSTANTS.SAT},
			{"Κυριακή": CONSTANTS.SUN}
		]
	}


@app.get("/help/codes/stops")
async def get_help_codes_stops():
	return {
		"STOP CODES": [
			{"Μπαλτατζή Μ": CONSTANTS.MPALTATZI_PROS},
			{"Μπαλτατζή Ε": CONSTANTS.MPALTATZI_APO},
			{"Δημοτική Μ": CONSTANTS.DIMOTIKI_PROS},
			{"Τσαλδάρη Μ": CONSTANTS.TSALDARI_PROS},
			{"Κωνσταντίνου & Ελένης Μ": CONSTANTS.KONEL_PROS},
			{"Κωνσταντίνου & Ελένης Ε": CONSTANTS.KONEL_APO},
			{"Τεχνική Σχολή (Λέσχη) Ε": CONSTANTS.TEXN_APO},
			{"Εστίες Μ": CONSTANTS.ESTIES_PROS},
			{"Τμήμα Ηλεκτρολόγων Μηχανικών Μ": CONSTANTS.HMMY_PROS},
			{"Τμήμα Ηλεκτρολόγων Μηχανικών Ε": CONSTANTS.HMMY_APO},
			{"Λεωφόρος Στρατού Μ": CONSTANTS.LEOF_STRATOU_PROS},
			{"Λεωφόρος Στρατού Ε": CONSTANTS.LEOF_STRATOU_APO},
			{"Τμήμα Πολιτικών Μηχανικών M": CONSTANTS.POL_PROS},
			{"Τμήμα Πολιτικών Μηχανικών E": CONSTANTS.POL_APO},
			{"Τμήμα Αρχιτεκτόνων M": CONSTANTS.ARCH_PROS},
			{"Τμήμα Αρχιτεκτόνων Ε": CONSTANTS.ARCH_APO},
			{"Τμήμα Μηχανικών Περιβάλλοντος (Εργαστήρια) Μ": CONSTANTS.ENV_PROS},
			{"Τμήμα Μηχανικών Περιβάλλοντος (Εργαστήρια) Ε": CONSTANTS.ENV_APO},
			{"Ξενοδοχείο Έλενα Ε": CONSTANTS.ELENA_APO},
			{"Προκάτ (Deprecated) Ε": CONSTANTS.PROKAT},
		]
	}



@app.post("/generate")
def generate_day_schedule():
	"""
	Fetches day schedule and savse it on disk for faster access and lower server network usage 
	Runs automatically @ 6 AM (+-5) minutes every day
	Refines itself every X hours
	No reason for a user to use this endpoint, it will return an error response
	"""
	today = datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%A-%d-%m-%Y")
	
	if(path.isfile(f"./app/logs/{today}.json")):
		return {"error": "today's schedule has already been registered."}
	
	token = fetch_token(CONSTANTS.PAGE_URL)

	headers = {
		"Content-Type": "application/json; charset=utf-8",
		'Authorization': f"Bearer {token}"
	}

	day = today.replace(' ','').split('-')[0]
	day_code = match_day(day)
	if type(day_code) != int:
		return {"error": "Error processing date -> day"}

	valid = []
	for stop in CONSTANTS.LINE_PATH:
		url = f"https://rest.citybus.gr/api/v1/el/104/trips/stop/{stop}/day/{day}"

		req = requests.get(
				url,
				headers=headers,
			)
		
		if req.status_code != 200:
			return {"error": "failed to fetch trip data"}

		resp = json.loads(req.text)

		for obj in resp:
			if obj["routeCode"] != CONSTANTS.ROUTE:
				continue
			try:
				valid.append({
					"stop": stop,
					"route": obj["routeCode"],
					"time": obj['tripTime']
					})
			except KeyError:
				continue

	with open(f"./app/logs/{today}.json", 'w', encoding="utf-8") as day_schedule:
		for el in valid:
			json.dump(el, day_schedule, ensure_ascii=False)
			day_schedule.write(',')
		
	return {"message": "succesfully created today's log file"}


@app.get("/next/{stop}")
def get_next(stop: str):
	"""
	Calculates the next arrival to said stop
	Usage: https://{domain-here}/next/{stop-code-here} 
	"""
	if not match_stop(stop):
		return {"error": "Υπάρχει σφάλμα στον κωδικό της στάσης"}

	today = datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%A-%d-%m-%Y")

	try:	
		t_schedule = {}
		with open(f"app/logs/{today}.json") as schedule:
			t_schedule = ast.literal_eval(schedule.read())
			
	except FileNotFoundError:
		return {"error": "Το σημερινό πρόγραμμα για κάποιο λόγο δεν είναι διαθέσιμο. Παρακαλώ επικοινωνήστε άμεσα με τον διαχειριστή."}
		

	now = datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%A %m %Y - %H:%M:%S").split('-')
	day = now[0].split(' ')[0]
	day_code = match_day(day)
	if type(day_code) != int:
		return {"error": "Error processing date -> day"}
	
	time = now[1].replace(' ','')
	proper_time = datetime.strptime(time, "%H:%M:%S")
	arrivals = []
	for el in t_schedule:
		if el['stop'] != stop:
			continue
		
		proper_arrival = datetime.strptime(el['time'], "%H:%M")
		if proper_arrival < proper_time:
			continue

		remaining = proper_arrival - proper_time
		arrivals.append(remaining)
	
	if len(arrivals) == 0:
		return {"message": "Δεν υπάρχουν άλλα διαθέσιμα δρομολόγια σήμερα για αυτή τη στάση."}
	
	return {"departs_in": str(min(arrivals))}


@app.get("/{stop}")
async def get_stops_today(stop: str) -> dict:
	"""
	Gets full arrival timetable for today.
	This endpoint uses the stored data, so there might be some variance
	with the real arrival times
	"""
	if not match_stop(stop):
		return {"error": "Υπάρχει σφάλμα στον κωδικό της στάσης"}
		
	today = datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%A-%d-%m-%Y")
	
	try:	
		t_schedule = {}
		with open(f"app/logs/{today}.json") as schedule:
			t_schedule = ast.literal_eval(schedule.read())
			
	except FileNotFoundError:
		return {"error": "Το σημερινό πρόγραμμα για κάποιο λόγο δεν είναι διαθέσιμο. Παρακαλώ επικοινωνήστε άμεσα με τον διαχειριστή."}
	
	now = datetime.now().replace(tzinfo=CONSTANTS.TZ).strftime("%A %m %Y - %H:%M:%S").split('-')
	day = now[0].split(' ')[0]
	day_code = match_day(day)
	if type(day_code) != int:
		return {"error": "Error processing date -> day"}
	
	time = now[1].replace(' ','')
	proper_time = datetime.strptime(time, "%H:%M:%S")
	arrivals = []
	for el in t_schedule:
		try:
			if el['stop'] != stop:
				continue

			arrivals.append(el['time'])
		except KeyError:
			continue

	name = match_stop(stop)
	return {
		"stop": name,
		"arrivals": arrivals
	}


@app.get("/{stop}/{day}")
def get_stops_by_day(stop: str, day: int) -> dict:
	"""
	Gets full arrival timetable for a certain stop and day combination 
	Usage: https://{domain-here}/{stop-code-here}/{day-code-here}
	This endpoint does not use the stored schedule, so it can access data
	straight from the official endpoint
	"""
	if not match_stop(stop):
		return {"error": "Υπάρχει σφάλμα στον κωδικό της στάσης"}

	if day > 6 or day < 0:
		return  {"error": "Υπάρχει σφάλμα στον κωδικό της ημέρας"}
		
	token = fetch_token(CONSTANTS.PAGE_URL)

	headers = {
		"Content-Type": "application/json; charset=utf-8",
		'Authorization': f"Bearer {token}"
	}

	url = f"https://rest.citybus.gr/api/v1/el/104/trips/stop/{stop}/day/{day}"

	req = requests.get(
			url,
			headers=headers,
		)
	
	resp = json.loads(req.text)
	valid = []

	for obj in resp:
		if obj["routeCode"] != CONSTANTS.ROUTE:
			continue
		try:
			valid.append(obj['tripTime'])
		except KeyError:
			continue

	name = match_stop(stop)
	return {
		'stop': name,
		'arrivals': valid
	}
