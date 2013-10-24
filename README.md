***************************************************************
*This is a part of openerp modul project modification by Csysc*
*created by Company System Controll Kft (Ltd)
*mail: csysc@csysc.eu
*auth.: Laszlo kozma
*date:  2013
*Use your own risk... // A használat csak saját felelősségre
***************************************************************

*Project Items:
*csysc_sales_order_row_tax 
/ *Features: Add a new record for the sales order report. // Áfa megjelenítése az értékesítési sorban
  *Tested at: Openerp 6.1
  *Know bugs:
- a report visszatölti magát a mentésekből.:
 (Ezt ki tudod kapcsolni a Beállítás/Testreszabás/Alacsony színtű objektumok/Műveletek/Jelentések menü alatt.
Keress rá a az objektum fül alatt az account.invoice -ra, majd az eredeti és a számlamásolat reportnál kattintsd ki a "Töltse újra csatolmányból" opcíót.
Itt tudod beállítani a céges fejlécet is ha akarod
  )

*csysc_extra_reports
/ *Features: Magyar számlakép.
  *Tested at: Openerp 6.1* 
  *Note: Az rml nyelv ismerete erősen ajánlott. (A cégek adatait kézzel kell kitölteni, 
  mert kivettem a res.company infókat kompatibilitási okokból, illetve mert nem müködtek )

*csysc_inh_account_inv_tax
/ *Features: Magyar számalkép kitöltő kiegészítés.
/ * Note: Részletek a modul leírásban

