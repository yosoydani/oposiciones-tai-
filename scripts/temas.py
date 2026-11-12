"""Asigna tema (1-33) a las preguntas de los bancos oficiales.

- Puntúa cada pregunta por palabras clave de cada tema (normas y términos propios).
- En la primera parte del cuestionario, las preguntas van en el orden del temario:
  se elige la secuencia de temas no decreciente que mejor encaja con las puntuaciones.
- Reservas y supuestos: el tema con más puntuación (dentro del bloque del supuesto);
  si nada encaja, queda sin tema (null).
Uso: python3 -I temas.py ../oposiciones-tai/data/bancos [--dry]
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

K = {
 1: ["corona", "sucesion al trono", "el rey", "la reina", "derechos fundamentales", "libertades publicas", "suspension de los derechos", "suspension de derechos", "titulo preliminar", "reforma constitucional", "estado social y democratico", "recurso de amparo", "principio de legalidad", "jerarquia normativa", "regente", "tutor del rey", "organizacion territorial", "titulo viii", "comunidades autonomas", "estatutos de autonomia"],
 2: ["cortes generales", "congreso", "senado", "diputacion permanente", "tribunal constitucional", "defensor del pueblo", "3/1981", "2/1979", "loreg", "5/1985", "diputados", "senadores", "iniciativa legislativa", "decreto-ley", "decreto legislativo", "ley organica 2/2026"],
 3: ["ley 50/1997", "50/1997", "del gobierno", "presidente del gobierno", "investidura", "mocion de censura", "cuestion de confianza", "consejo de ministros", "vicepresident", "comisiones delegadas", "gobierno en funciones", "plan anual normativo"],
 4: ["5/2015", "empleado publico", "estatuto basico", "funcionario", "personal laboral", "19/2013", "transparencia", "buen gobierno", "agenda 2030", "desarrollo sostenible", "53/1984", "incompatibilidades", "situaciones administrativas", "carrera profesional", "permisos", "excedencia", "consejo de transparencia"],
 5: ["igualdad", "3/2007", "violencia de genero", "1/2004", "lgtbi", "4/2023", "personas trans", "discapacidad", "1/2013", "situacion de dependencia", "personas en situacion de dependencia", "39/2006", "violencia sobre la mujer", "15/2022", "no discriminacion"],
 6: ["sociedad de la informacion", "34/2002", "lssi", "firma electronica", "6/2020", "eidas", "910/2014", "dni electronico", "dnie", "dnie v3.0", "dnie 4.0", "dni 4.0", "certificado cualificado", "certificados cualificados", "agenda digital", "espana digital", "sello de tiempo", "sello electronico", "prestador de servicios de confianza", "255/2025", "1553/2005", "identidad digital"],
 7: ["proteccion de datos", "rgpd", "2016/679", "3/2018", "lopdgdd", "derechos digitales", "delegado de proteccion", "datos personales", "responsable del tratamiento", "encargado del tratamiento", "agencia espanola de proteccion"],
 8: ["39/2015", "40/2015", "procedimiento administrativo", "203/2021", "esquema nacional de seguridad", "311/2022", "esquema nacional de interoperabilidad", "4/2010", "norma tecnica de interoperabilidad", "normas tecnicas de interoperabilidad", "expediente electronico", "documento electronico", "actuacion administrativa automatizada", "notificaciones electronicas", "1125/2024"],
 9: ["sede electronica", "cl@ve", "intermediacion de datos", "registro electronico", "209/2003", "registros y las notificaciones", "face", "autofirma", "geiser", "orve", "sistema de interconexion de registros", "notific@", "carpeta ciudadana", "red sara", "punto de acceso general", "infraestructuras y servicios comunes", "@firma", "inside", "archive", "ctt", "centro de transferencia"],
 10: ["cache", "procesador", "cpu", "bus del sistema", "memoria ram", "memoria principal", "von neumann", "harvard", "alu", "unidad de control", "complemento a 2", "complemento a dos", "binario", "hexadecimal", "octal", "ascii", "unicode", "utf-8", "ieee 754", "coma flotante", "bios", "uefi", "placa base", "chipset", "risc", "cisc", "registro de instrucciones", "contador de programa", "dram", "sram", "eeprom", "nucleo del procesador"],
 11: ["periferic", "ssd", "estado solido", "disco duro", "hdmi", "displayport", "usb", "thunderbolt", "raid", "impresora", "printing protocol", "ipp", "escaner", "monitor", "pantalla", "tarjeta grafica", "nvme", "sata", "teclado", "raton", "ppp", "dpi", "oled", "lcd", "cinta", "lto", "almacenamiento optico", "blu-ray"],
 12: ["csv", "rfc 4180", "json", "rfc 8259", "algoritmo de ordenacion", "algoritmos de ordenacion", "ordenacion", "arbol", "rojo-negro", "pila", "cola de prioridad", "lista enlazada", "tabla hash", "funcion hash", "fichero", "ficheros", "formato de", "jpeg", "png", "gif", "svg", "mp3", "mp4", "codec", "compresion", "grafo", "quicksort", "mergesort", "busqueda binaria", "complejidad", "o(n", "estructura de datos", "estructuras de datos", "greedy", "voraz", "backtracking"],
 13: ["sistema operativo", "sistemas operativos", "android", "ios", "kernel de linux", "nucleo del sistema", "planificacion de procesos", "planificador", "memoria virtual", "paginacion", "interbloqueo", "semaforo", "proceso", "hilo", "ntfs", "ext4", "fat32", "exfat", "apfs", "sandbox", "macos", "windows 11"],
 14: ["nosql", "cypher", "neo4j", "mongodb", "cassandra", "redis", "orientadas a objetos", "orientada a objetos", "oid", "sgbd", "data warehouse", "almacen de datos", "kimball", "inmon", "olap", "oltp", "dimensional", "big data", "data lake", "data mining", "mineria de datos", "acid", "base", "teorema cap", "clave-valor", "documental", "columnar", "outrigger", "cubo", "orm", "mapeador objeto-relacional", "reglas de codd", "codd"],
 15: ["entidad-relacion", "entidad relacion", "cardinalidad", "grado", "atributo", "normalizacion", "forma normal", "clave primaria", "clave foranea", "clave candidata", "modelo relacional", "algebra relacional", "diagrama e/r", "dependencia funcional", "integridad referencial", "entidad debil", "superclave", "tupla", "dominio"],
 16: ["javascript", "python", "operador", "expresion", "recursiv", "lenguaje de programacion", "lenguajes de programacion", "compilador", "interprete", "tipo de dato", "tipos de datos", "bucle", "paso por valor", "paso por referencia", "variable", "funcion lambda", "c++", "typescript", "go ", "rust", "kotlin", "tipado"],
 17: ["sql", "select", "insert", "update", "delete from", "join", "deny", "grant", "revoke", "commit", "rollback", "savepoint", "trigger", "disparador", "procedimiento almacenado", "procedimientos almacenados", "transact-sql", "pl/sql", "create table", "ddl", "dml", "dcl", "tcl", "having", "group by", "vista", "cursor", "transaccion"],
 18: ["patron de diseno", "patrones de diseno", "patron", "observer", "observador", "singleton", "factory", "decorator", "adapter", "strategy", "uml", "herencia", "polimorfismo", "sobrescritura", "sobrecarga", "encapsulacion", "clase abstracta", "interfaz", "diagrama de clases", "diagrama de secuencia", "casos de uso", "gof", "orientada a objetos", "subclase", "superclase", "solid"],
 19: ["java ee", "jakarta", "jvm", "maquina virtual de java", "jit", "just-in-time", ".net", "clr", "ensamblado", "c#", "spring", "maven", "gradle", "servlet", "jsp", "jsf", "ejb", "jpa", "hibernate", "tomcat", "catalina", "asp.net", "cil", "msil", "nuget", "linq", "blazor", "java"],
 20: ["cliente/servidor", "cliente-servidor", "multicapa", "tres capas", "n capas", "servicio web", "servicios web", "soap", "wsdl", "rest", "restful", "openapi", "swagger", "graphql", "uddi", "idempotente", "middleware", "api", "grpc", "soa"],
 21: ["html", "css", "dom", "doctype", "whatwg", "ajax", "fetch", "navegador", "xml", "xslt", "xpath", "dtd", "xsd", "elemento raiz", "php", "angular", "react", "vue", "node.js", "web front", "front-end", "frontend", "cookie", "localstorage", "webassembly", "pwa", "lenguaje de marcas", "w3c"],
 22: ["accesibilidad", "wcag", "1112/2018", "usabilidad", "diseno universal", "owasp", "xss", "cross-site", "inyeccion", "desarrollo seguro", "aria", "lector de pantalla", "en 301 549", "11/2023", "csrf", "autenticacion multi-factor", "mfa", "punto de usuario final"],
 23: ["git", "pull request", "repositorio", "control de versiones", "pruebas de software", "prueba de software", "pruebas unitarias", "prueba unitaria", "junit", "selenium", "jmeter", "metodologia", "scrum", "agil", "kanban", "metrica", "devops", "integracion continua", "github", "gitlab", "jenkins", "documentacion", "caja blanca", "caja negra", "pruebas de regresion", "sonarqube", "commit", "branch", "merge"],
 24: ["crontab", "cron", "tail", "systemctl", "systemd", "bash", "shell", "powershell", "directorio activo", "active directory", "gpo", "directiva de grupo", "chmod", "chown", "usuarios y grupos", "rhel", "red hat", "ldap", "windows server", "comando", "sudo", "journalctl", "/etc/", "unidad organizativa", "controlador de dominio", "linux", "registro de windows", "dnf", "yum", "apt", "puertos en escucha", "auditd", "firewall-cmd", "robocopy", "xcopy"],
 25: ["virtualizacion", "hipervisor", "maquina virtual", "snapshot", "copia de seguridad", "copias de seguridad", "backup", "3-2-1", "san", "nas", "lvm", "volumen logico", "administracion de bases de datos", "tablespace", "rman", "vmware", "hyper-v", "kvm", "proxmox", "copia incremental", "copia diferencial", "deduplicacion", "iscsi", "fibre channel", "tar "],
 26: ["correo", "smtp", "imap", "pop3", "dmarc", "spf", "dkim", "exchange", "postfix", "docker", "contenedor", "contenedores", "kubernetes", "microservicio", "microservicios", "podman", "pod", "plano de control", "kubelet", "helm", "dockerfile", "mta", "mua"],
 27: ["switch", "conmutador", "mac sticky", "sticky", "port security", "seguridad de puertos", "snmp", "monitorizacion", "wireshark", "netflow", "sniffer", "dhcp", "administracion de red", "trafico de red", "rmon", "syslog", "nagios", "zabbix", "mib"],
 28: ["vulnerabilidad", "vulnerabilidades", "cve", "malware", "ransomware", "ccn-cert", "ccn", "contrasena", "cpd", "centro de proceso de datos", "centro de procesamiento de datos", "tia 942", "tia-942", "criptograf", "cifrado", "aes", "rsa", "sha-", "incidente", "incidentes", "nis2", "auditoria", "analisis de riesgos", "magerit", "pilar", "seguridad fisica", "seguridad logica", "key exchange", "troyano", "gusano", "botnet", "siem", "itil", "firma digital", "gestion de servicios"],
 29: ["conmutacion de circuitos", "conmutacion de paquetes", "fibra optica", "par trenzado", "coaxial", "wifi", "wi-fi", "802.11", "5g", "4g", "lte", "bluetooth", "radio", "satelite", "gpon", "ftth", "xdsl", "adsl", "medios de transmision", "antena", "inalambric", "movil", "red movil", "espectro", "modulacion", "multiplexacion", "zigbee", "lora"],
 30: ["osi", "capa de", "tcp/ip", "ipv4", "ipv6", "subred", "subredes", "mascara", "cidr", "tcp", "udp", "icmp", "arp", "rfc 8200", "hop limit", "cabecera ip", "direccion ip", "enrutamiento", "ospf", "bgp", "rip", "nat", "ttl", "hosts", "direccion de red", "broadcast", "difusion", "red interna", "next hop", "tabla de enrutamiento"],
 31: ["http", "https", "tls", "ssl", "codigos de estado", "codigo de estado", "url", "dns", "internet", "http/2", "http/3", "quic", "world wide web", "uri", "hsts", "certificado digital del servidor", "cdn", "protocolo tls", "version estable del protocolo tls"],
 32: ["cortafuegos", "firewall", "dmz", "zona desmilitarizada", "vpn", "ipsec", "pharming", "phishing", "puesto del usuario", "puesto de usuario", "antivirus", "proxy", "ids", "ips", "acceso remoto", "radius", "tacacs", "802.1x", "perimetral", "bastion", "edr", "nac", "spoofing", "waf", "byod", "mdm", "gestion de dispositivos moviles", "l2tp", "pptp", "vpn de nivel de enlace", "codigo danino"],
 33: ["topologia", "terminador", "ethernet", "802.3", "csma", "token ring", "spanning tree", "stp", "802.1q", "vlan", "hub (concentrador)", "concentrador", "puente", "cableado estructurado", "categoria 6", "cat 6", "rj45", "red de area local", "lan", "repetidor", "dominio de colision", "dominio de difusion", "router"],
}
KN = {t: [norm(k) for k in ks] for t, ks in K.items()}

def score(text):
    t = norm(text)
    s = {n: 0.0 for n in K}
    for n, ks in KN.items():
        for k in ks:
            if re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", t) if k[0].isalnum() and k[-1].isalnum() else k in t:
                s[n] += 3.0 if re.search(r"\d+/\d{4}", k) else (1.5 if len(k) > 10 else 1.0)
    # Artículos de la Constitución
    if "constitucion" in t:
        for m in re.finditer(r"articulos? (\d+)", t):
            a = int(m.group(1))
            if a <= 55 or 56 <= a <= 65 or a >= 166:
                s[1] += 3
            elif a == 54 or 66 <= a <= 96 or 159 <= a <= 165:
                s[2] += 3
            elif 97 <= a <= 116:
                s[3] += 3
    return s

def best_monotone(scores):
    """Secuencia no decreciente de temas que maximiza la suma; cada cambio cuesta un poco."""
    temas = sorted(K)
    n = len(scores)
    INF = float("-inf")
    dp = [[INF] * len(temas) for _ in range(n)]
    bk = [[0] * len(temas) for _ in range(n)]
    for j, t in enumerate(temas):
        dp[0][j] = scores[0][t] - 0.02 * j
    for i in range(1, n):
        for j, t in enumerate(temas):
            best, arg = INF, 0
            for k in range(len(temas)):
                if k > j:  # retroceder en el temario: posible, pero caro
                    v = dp[i - 1][k] - 2.5
                    if v > best:
                        best, arg = v, k
                    continue
                v = dp[i - 1][k] - (0 if k == j else 0.05 + 0.01 * (j - k))  # avanzar es barato
                if v > best:
                    best, arg = v, k
            dp[i][j] = best + scores[i][t]
            bk[i][j] = arg
    j = max(range(len(temas)), key=lambda x: dp[n - 1][x])
    out = [0] * n
    for i in range(n - 1, -1, -1):
        out[i] = temas[j]
        j = bk[i][j]
    return out

def texto(q):
    return q["enunciado"] + " " + " ".join(q["opciones"])

def main():
    d = Path(sys.argv[1])
    dry = "--dry" in sys.argv
    stats = {"asignadas": 0, "sin_tema": 0}
    for f in sorted(d.glob("oficial-*.json")):
        b = json.loads(f.read_text(encoding="utf-8"))
        qs = b["preguntas"]
        if b["parte"] == "cuestionario":
            main_qs = [q for q in qs if not q.get("reserva")]
            seq = best_monotone([score(texto(q)) for q in main_qs])
            for q, t in zip(main_qs, seq):
                q["tema"] = t
                q["tema_auto"] = True
            rest = [q for q in qs if q.get("reserva")]
            allowed = set(K)
        else:
            rest = qs
            allowed = set(range(14, 24)) if b["parte"] == "supuesto1" else set(range(10, 15)) | set(range(24, 34))
        for q in rest:
            s = score(texto(q))
            cand = max(allowed, key=lambda t: s[t])
            q["tema"] = cand if s[cand] > 0 else None
            q["tema_auto"] = True
        for q in qs:
            stats["asignadas" if q["tema"] is not None else "sin_tema"] += 1
        if not dry:
            f.write_text(json.dumps(b, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(stats)

if __name__ == "__main__":
    main()
