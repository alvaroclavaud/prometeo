# Catálogo base de Prometeo: políticos, medios, temas, provincias y partidos.
# Se edita aquí (o desde el panel, que guarda cambios en la base de datos).
import json, re

POL = [
 # id, nombre, partido, ámbito, cargo, territorio, alias en titulares
 ('sanchez','Pedro Sánchez','PSOE','Gobierno','Presidente del Gobierno y candidato del PSOE','España',['Pedro Sánchez','Sánchez']),
 ('feijoo','Alberto Núñez Feijóo','PP','Oposición','Presidente del PP y candidato','España',['Feijóo','Feijoo']),
 ('abascal','Santiago Abascal','Vox','Oposición','Presidente de Vox y candidato','España',['Abascal']),
 ('cuerpo','Carlos Cuerpo','PSOE','Gobierno','Ministro de Economía, Comercio y Empresa','España',['Carlos Cuerpo','Cuerpo']),
 ('diaz','Yolanda Díaz','Sumar','Gobierno','Vicepresidenta segunda y ministra de Trabajo','España',['Yolanda Díaz']),
 ('aagesen','Sara Aagesen','PSOE','Gobierno','Vicepresidenta tercera y ministra para la Transición Ecológica','España',['Aagesen']),
 ('bolanos','Félix Bolaños','PSOE','Gobierno','Ministro de la Presidencia y Justicia','España',['Bolaños']),
 ('espana','Arcadi España','PSOE','Gobierno','Ministro de Hacienda','España',['Arcadi España']),
 ('albares','José Manuel Albares','PSOE','Gobierno','Ministro de Asuntos Exteriores','España',['Albares']),
 ('robles','Margarita Robles','PSOE','Gobierno','Ministra de Defensa','España',['Margarita Robles','Robles']),
 ('marlaska','Fernando Grande-Marlaska','PSOE','Gobierno','Ministro del Interior','España',['Marlaska']),
 ('puente','Óscar Puente','PSOE','Otros','Exministro de Transportes','España',['Óscar Puente','Puente']),
 ('garcia','Mónica García','Más Madrid','Gobierno','Ministra de Sanidad','España',['Mónica García']),
 ('cerdan','Santos Cerdán','PSOE','Otros','Ex secretario de Organización del PSOE','Navarra',['Cerdán']),
 ('gamarra','Cuca Gamarra','PP','Oposición','Vicesecretaria del PP','España',['Gamarra']),
 ('tellado','Miguel Tellado','PP','Oposición','Secretario general del PP','España',['Tellado']),
 ('millan','Pepa Millán','Vox','Oposición','Portavoz de Vox en el Congreso','España',['Pepa Millán','Millán']),
 ('ayuso','Isabel Díaz Ayuso','PP','Autonómico','Presidenta de la Comunidad de Madrid','Madrid',['Ayuso']),
 ('moreno','Juan Manuel Moreno Bonilla','PP','Autonómico','Presidente de la Junta de Andalucía','Andalucía',['Juanma Moreno','Moreno Bonilla','Juan Manuel Moreno','Moreno']),
 ('illa','Salvador Illa','PSC','Autonómico','President de la Generalitat de Catalunya','Cataluña',['Salvador Illa','Illa']),
 ('pradales','Imanol Pradales','PNV','Autonómico','Lehendakari','País Vasco',['Pradales']),
 ('rueda','Alfonso Rueda','PP','Autonómico','Presidente de la Xunta de Galicia','Galicia',['Alfonso Rueda','Rueda']),
 ('page','Emiliano García-Page','PSOE','Autonómico','Presidente de Castilla-La Mancha','Castilla-La Mancha',['García-Page','Page']),
 ('mazon','Carlos Mazón','PP','Otros','Expresidente de la Generalitat Valenciana','Comunidad Valenciana',['Mazón']),
 ('puigdemont','Carles Puigdemont','Junts','Otros','Presidente de Junts','Cataluña',['Puigdemont']),
 ('rufian','Gabriel Rufián','ERC','Oposición','Portavoz de ERC en el Congreso','Cataluña',['Rufián']),
 ('nogueras','Míriam Nogueras','Junts','Oposición','Portavoz de Junts en el Congreso','Cataluña',['Nogueras']),
 ('otegi','Arnaldo Otegi','EH Bildu','Otros','Coordinador general de EH Bildu','País Vasco',['Otegi']),
 ('esteban','Aitor Esteban','PNV','Otros','Presidente del PNV','País Vasco',['Aitor Esteban']),
 ('belarra','Ione Belarra','Podemos','Oposición','Secretaria general de Podemos','España',['Belarra']),
 ('montero_mj','María Jesús Montero','PSOE','Otros','Vicesecretaria general del PSOE y líder del PSOE andaluz','Andalucía',['María Jesús Montero','Montero']),
 ('alegria','Pilar Alegría','PSOE','Otros','Líder del PSOE de Aragón','Aragón',['Pilar Alegría','Alegría']),
 ('urtasun','Ernest Urtasun','Sumar','Gobierno','Ministro de Cultura','España',['Urtasun']),
 ('saiz','Elma Saiz','PSOE','Gobierno','Ministra de Inclusión y portavoz del Gobierno','España',['Elma Saiz','Saiz']),
 ('torres','Ángel Víctor Torres','PSOE','Gobierno','Ministro de Política Territorial','España',['Ángel Víctor Torres','Torres']),
 ('redondo','Ana Redondo','PSOE','Gobierno','Ministra de Igualdad','España',['Ana Redondo','Redondo']),
 ('semper','Borja Sémper','PP','Oposición','Portavoz nacional del PP','España',['Sémper']),
 ('funez','Carmen Fúnez','PP','Oposición','Vicesecretaria del PP','España',['Fúnez']),
 ('bendodo','Elías Bendodo','PP','Oposición','Vicesecretario del PP','España',['Bendodo']),
 ('buxade','Jorge Buxadé','Vox','Oposición','Eurodiputado de Vox','España',['Buxadé']),
 ('garriga','Ignacio Garriga','Vox','Oposición','Secretario general de Vox','España',['Garriga']),
 ('almeida','José Luis Martínez-Almeida','PP','Local','Alcalde de Madrid','Madrid',['Almeida']),
 ('collboni','Jaume Collboni','PSC','Local','Alcalde de Barcelona','Cataluña',['Collboni']),
 ('guardiola','María Guardiola','PP','Autonómico','Presidenta de la Junta de Extremadura','Extremadura',['María Guardiola','Guardiola']),
 ('azcon','Jorge Azcón','PP','Autonómico','Presidente de Aragón','Aragón',['Azcón']),
 ('prohens','Marga Prohens','PP','Autonómico','Presidenta de las Illes Balears','Illes Balears',['Prohens']),
 ('clavijo','Fernando Clavijo','CC','Autonómico','Presidente de Canarias','Canarias',['Clavijo']),
 ('aragones','Pere Aragonès','ERC','Otros','Expresident de la Generalitat','Cataluña',['Aragonès','Aragonés']),
 ('matute','Oskar Matute','EH Bildu','Oposición','Portavoz de EH Bildu en Madrid','País Vasco',['Matute']),
 ('montero_i','Irene Montero','Podemos','Oposición','Eurodiputada y candidata de Podemos','España',['Irene Montero']),
]

PARTIDOS = {  # color de identificación (punto junto al nombre)
 'PSOE':'#d9342b','PSC':'#d9342b','PP':'#1f6fc4','Vox':'#5aa81d','Sumar':'#d6246e','Más Madrid':'#16a891','Podemos':'#7a52b8',
 'Junts':'#12a39a','ERC':'#e29a12','PNV':'#1f7a45','EH Bildu':'#8fae1b','CC':'#c9a400',
}

MED = [  # id, nombre, dominio, tipo
 ('elespanol','El Español','elespanol.com','Prensa'),('as','Diario AS','as.com','Prensa'),('elmundo','El Mundo','elmundo.es','Prensa'),
 ('elpais','El País','elpais.com','Prensa'),('marca','Marca','marca.com','Prensa'),('abc','ABC','abc.es','Prensa'),
 ('elconfidencial','El Confidencial','elconfidencial.com','Prensa'),('elperiodico','El Periódico','elperiodico.com','Prensa'),
 ('rtve','RTVE','rtve.es','Radio y TV'),('okdiario','OKdiario','okdiario.com','Prensa'),('20minutos','20 Minutos','20minutos.es','Prensa'),
 ('antena3','Antena 3 Noticias','antena3.com','Radio y TV'),('ser','Cadena SER','cadenaser.com','Radio y TV'),('lasexta','La Sexta','lasexta.com','Radio y TV'),
 ('cope','COPE','cope.es','Radio y TV'),('telecinco','Telecinco','telecinco.es','Radio y TV'),('ondacero','Onda Cero','ondacero.es','Radio y TV'),
]

TEM = [  # id, nombre, foco territorial, regex de titulares, ventana del mapa
 ('inseguridad','Inseguridad',['Ceuta'],r'insegur|delincuen|criminal|\brobo|atraco|okupa|narco|apuñal|tiroteo|homicid|asesin|agresi[oó]n|violaci[oó]n|detenid|\bbanda','7 días'),
 ('economia','Economía',['Madrid','Barcelona'],r'econom|empleo|\bparo\b|vivienda|alquiler|inflaci|precio|salario|pension|impuest|hipoteca|\bPIB\b|eur[ií]bor|presupuest|huelga','2 días'),
 ('inmigracion','Inmigración',['España'],r'inmigra|migrant|patera|cayuco|menores no acompañados|\bmenas\b|frontera|asilo|deportac|regulariza','7 días'),
 ('campana','Campaña 29-N',['España'],r'eleccion|29-?N|campaña|sondeo|encuesta|mitin|debate|candidat|\bvoto|urnas|escaños',''),
]

PROV = [  # código INE, nombre, población aprox. (miles, INE 2024 redondeado)
 ('01','Álava',340),('02','Albacete',390),('03','Alicante',1990),('04','Almería',760),('05','Ávila',160),('06','Badajoz',665),('07','Illes Balears',1230),
 ('08','Barcelona',5880),('09','Burgos',360),('10','Cáceres',388),('11','Cádiz',1255),('12','Castellón',615),('13','Ciudad Real',492),('14','Córdoba',770),
 ('15','A Coruña',1130),('16','Cuenca',198),('17','Girona',820),('18','Granada',935),('19','Guadalajara',280),('20','Gipuzkoa',730),('21','Huelva',535),
 ('22','Huesca',228),('23','Jaén',620),('24','León',447),('25','Lleida',450),('26','La Rioja',325),('27','Lugo',325),('28','Madrid',7000),('29','Málaga',1775),
 ('30','Murcia',1570),('31','Navarra',678),('32','Ourense',304),('33','Asturias',1010),('34','Palencia',158),('35','Las Palmas',1160),('36','Pontevedra',945),
 ('37','Salamanca',327),('38','Santa Cruz de Tenerife',1080),('39','Cantabria',590),('40','Segovia',157),('41','Sevilla',1970),('42','Soria',90),
 ('43','Tarragona',850),('44','Teruel',135),('45','Toledo',740),('46','Valencia',2710),('47','Valladolid',525),('48','Bizkaia',1155),('49','Zamora',166),
 ('50','Zaragoza',990),('51','Ceuta',83),('52','Melilla',86),
]

NIVEL1 = ['sanchez','feijoo','abascal']
ELECCIONES = {'fecha':'2026-11-29','nombre':'Elecciones generales 29-N','inicio_campana':'2026-11-13'}

def alias_re(alias):
    return re.compile(r'(?<![\wÀ-ÿ])(' + '|'.join(re.escape(a) for a in alias) + r')(?![\wÀ-ÿ])')

def catalogo(cfg=None):
    q = {p[0]: p for p in (cfg['pol'] if cfg else [])}
    return {
      'politicos': [{'id':i,'nombre':n,'partido':pa,'ambito':am,'cargo':ca,'territorio':te,'alias':al,
                     'consulta': q[i][1] if i in q else '"'+n+'"', 'wiki': q[i][2] if i in q else n} for (i,n,pa,am,ca,te,al) in POL],
      'partidos': PARTIDOS,
      'medios': [{'id':i,'nombre':n,'dominio':d,'tipo':t} for (i,n,d,t) in MED],
      'temas': [{'id':i,'nombre':n,'foco':f,'patron':r,'ventana':v, 'consulta': next((t[1] for t in (cfg['tem'] if cfg else []) if t[0]==i), '')} for (i,n,f,r,v) in TEM],
      'provincias': [{'id':c,'nombre':n,'pob':p} for (c,n,p) in PROV],
      'nivel1': NIVEL1, 'elecciones': ELECCIONES,
    }

if __name__ == '__main__':
    print(json.dumps(catalogo(), ensure_ascii=False)[:400])
