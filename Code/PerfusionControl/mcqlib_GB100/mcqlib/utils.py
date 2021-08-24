import xml.etree.ElementTree as ET

# def read_data_xml():
# 	tree = ET.parse('Data.xml')
# 	gasItems = tree.findall("./gasTable/gasItem")
# 	for gasItem in gasItems:
		
# 		gasId = gasItem.get("Id")
# 		gasType = gasItem.find("gasType").text
# 		# convertiamo i separatori decimali , >> .
# 		kfactor = get_float(gasItem.find("kfactor").text)

# 		print(gasId, gasType, kfactor)

# 	return 0

def get_gas_xml():
	#print(os.getcwd())
	tree = ET.parse('./mcqlib/Data.xml')
	gasItems = tree.findall("./gasTable/gasItem")

	gasDictionary = {}

	for gasItem in gasItems:
		
		gasId = int(gasItem.get("Id"))
		gasType = gasItem.find("gasType").text
		# convertiamo i separatori decimali , >> .
		kfactor = get_float(gasItem.find("kfactor").text)

		gasDictionary[gasId] = kfactor

	#print(gasDictionary)

	return gasDictionary

def get_custom_gas_xml():
	#print(os.getcwd())
	tree = ET.parse('./mcqlib/CustomData.xml')
	gasItems = tree.findall("./gasItem")

	gasDictionary = {}

	for gasItem in gasItems:
		
		gasId = int(gasItem.get("Id"))
		gasType = gasItem.find("gasType").text
		# convertiamo i separatori decimali , >> .
		kfactor = get_float(gasItem.find("kfactor").text)

		gasDictionary[gasId] = kfactor

	#print(gasDictionary)

	return gasDictionary

def get_gas_type(gas_id):
	#print(os.getcwd())
	tree = ET.parse('./mcqlib/Data.xml')
	gasItems = tree.findall("./gasTable/gasItem")

	gasDictionary = {}

	for gasItem in gasItems:
		
		gasId = int(gasItem.get("Id"))
		gasType = gasItem.find("gasType").text
		# convertiamo i separatori decimali , >> .
		kfactor = get_float(gasItem.find("kfactor").text)

		gasDictionary[gasId] = gasType


	try:
		return gasDictionary[gas_id]
	except Exception as e:
		return "N/A"
	

# rappresentazione binaria di decimale
def dec_to_bin(x):
  return int(bin(x)[2:])

# rappresentazione decimale di binario
def bin_to_dec(x):
  return int(x,2)
		
#nel file XML i float sono salvati con separatore decimale (,)
def get_float(x):		
	return float(str.replace(x, ",", "."))


def validate_sccm(sccm):
	if sccm > 0 and sccm < 6000:
		return True
	
	return False

# la lib ritorna un array di 2 word (int16)
# vanno considerati sequenzialmente e trasformati in un int unico 
# !!!! di cui le ultime 2 cifre sono decimali !!!
def sccm_response_to_float(response_sccm):
	bin_1 = dec_to_bin(response_sccm[0])
	bin_2 = dec_to_bin(response_sccm[1])

	bin_concat = str(bin_1) + str(bin_2)

	dec_value = bin_to_dec(bin_concat)

	float_value = dec_value / 100

	return float_value


# la lib ritorna un array di 2 word (int16)
# vanno considerati sequenzialmente e trasformati in un int unico
def sccm_response_to_int(response_sccm):
	bin_1 = dec_to_bin(response_sccm[0])
	bin_2 = dec_to_bin(response_sccm[1])

	bin_concat = str(bin_1) + str(bin_2)

	dec_value = bin_to_dec(bin_concat)

	return dec_value

#ritorna un array di possibili status
def mb_status(dec):
	status_values = []

	b = dec_to_bin(dec)
	
	#array di stringhe bit 0/1
	array_chars = list(str(b))
	
	#print(array_chars)
	
	if dec > 0:	
		if array_chars[0] == "1":
			status_values.append("System Ready")
			
		if array_chars[1] == "1":
			status_values.append("System connected with PC")
			
		if array_chars[2] == "1":
			status_values.append("Control ON - Gas Flowing")
			
		if array_chars[3] == "1":
			status_values.append("At least a Gas Channel Present")
		
	return status_values
	
	
#ritorna un array di possibili alert
def mb_alert(dec):
	values = []

	b = dec_to_bin(dec)
	
	#array di stringhe bit 0/1
	array_chars = list(str(b))	

	if dec > 0:
		if array_chars[0] == "1":
			values.append("Generic Error")
			
		if array_chars[4] == "1":
			values.append("Wrong Parameter")
			
		if array_chars[5] == "1":
			values.append("Serial Number Error")
			
		if array_chars[7] == "1":
			values.append("Warranty Error")
		
	return values

#ritorna un array di possibili alert
def channel_alert(dec):
	values = []

	b = dec_to_bin(dec)
	
	#array di stringhe bit 0/1
	array_chars = list(str(b))	

	if dec > 0:
		if array_chars[0] == "1":
			values.append("Generic Error")
			
		if array_chars[1] == "1":
			values.append("Calibration Error")
			
		if array_chars[2] == "1":
			values.append("Wrong address")
			
		if array_chars[3] == "1":
			values.append("Sensor Error")

		if array_chars[15] == "1":
			values.append("Link Error with this module")
		
	return values



# #ritorna un array di possibili alert
# def get_flow(current_flow):

# 	value = current_flow + (random.randint(0,15) * random.randint(-1,1))
	
# 	if value < 0:
# 		value = 0
	
# 	return value
	
	
	
	
	
	


# gas_types = {
# 	0  : "",
# 	1  : "Air",
# 	2  : "Nitrogen N2",
# 	3  : "Oxygen O2",
# 	4  : "Carbon Dioxide CO2",
# 	5  : "Carbon Monoxide CO",
# 	6  : "Nitric Oxide NO",
# 	7  : "Hydrogen H2",
# 	8  : "Helium He",
# 	9  : "Argon Ar",
# 	10 : "Methane CH4",
# 	11 : "Ethylene C2H4",
# 	12 : "Ethane C2H6"
# }

# max_flow_single_channel = 10000