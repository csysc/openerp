{
	"name" : "csysc_hungarian_invoice",
	"version" : "1.0",
	"author" : "Company System Controll LTD",
	"website" : "",
	"category" : "Generic Modules/Others",
	"depends" : ["base","account"],
	"description" : """
	original_name: csysc_inherit_inv_tax
	
	Magyar számla modul
	
	Főbb modul funkcíók:
		-   Számlasoronkénti Áfa számítás
		-	Valutás számlánál az adó váltásához külön árfolyam, dátummal
		-	Modosító számla készítése
		-	Érvénytelenítő számla készítése
		-	Teljesítés dátumának megadása
		-	Pénzforgalmi számla készítése
		-	Eredeti számla készítése
		-	Számlamásolat előállítása
	
	Számlakép:
	
	csysc_extra_reports modul tartalmazza
		-	Soronkénti Áfa számítása
		-	Valutás számlán Áfa összesítés Ft-ban
		-	Pénzforgalmi felirat
		-	Rendelkező előírások, megfeleltetések
		-	A számlakép a modul alatt van tárolva a report könyvtárban rml formátumban
		
	A jelentések alapállapotban a csatolmányokból visszatöltődnek. Ha módosítasz akkor:
		-	csak az új számlán látszik amit ügyeskedsz
		-	vagy látogasd meg a Settings / Customization / Low Level object / Actions / Reports menüt
				az Objectbe üsd be hogy "invo" (idézőjelek nélkűl) majd keress. Nyisd meg a reportot, és kattintsd ki a 
				Reload from Attachment jelőlést. Generáld le a reportot. Ha minden ok akkor látnod kell a változást.
				Ha mégsem, akkor küldj mailt, a  // csysc kukac csysc pont eu  // ra.
				
	A modul telepítése semmiféle garanciát sem jelent.
	
	Ha Apeh szerinti állásfoglalás is kell, akkor keress meg. 

	""",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : ["account_invoice_view.xml"],
	"active": False,
	"installable": True
}
