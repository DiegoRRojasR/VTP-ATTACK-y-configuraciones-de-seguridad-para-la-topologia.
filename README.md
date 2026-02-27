# Informe Técnico:  Ataque del protocolo VTP

## Video demostrativo

[![Ver video en YouTube](https://img.youtube.com/vi/wvEJ_TaGyrc/maxresdefault.jpg)](https://www.youtube.com/watch?v=wvEJ_TaGyrc)

---

## I-) Objetivo del Script de Explotación

El propósito fundamental de este script es demostrar la debilidad inherente en el proceso de actualización de la base de datos de VLANs en redes que utilizan VTP Versión 2. La herramienta está diseñada para realizar una inyección de paquetes de actualización (Summary y Subset Advertisements) con un número de revisión superior al actual en el switch objetivo. Al enviar una revisión más alta junto con un hash MD5 calculado específicamente para la nueva base de datos, el script obliga al switch a sobrescribir su configuración de VLANs local. El objetivo final es purgar las VLANs legítimas de la red y sustituirlas por una base de datos controlada por el atacante, lo que puede derivar en una denegación de servicio masiva o en la reestructuración no autorizada del tráfico segmentado.

<img width="661" height="832" alt="Screenshot 2026-02-27 160249" src="https://github.com/user-attachments/assets/964e0d7c-b1e0-45ef-8e55-927396cbd25e" />

---

## II-)Topología y Escenario de Red

La infraestructura de red bajo prueba utiliza un dominio VTP denominado exonereme.local. En este escenario, el atacante se conecta a un puerto de switch que ha sido previamente negociado como troncal (mediante DTP) o que se encuentra mal configurado. 

<img width="571" height="564" alt="Screenshot 2026-02-27 161748" src="https://github.com/user-attachments/assets/acdf81fd-d518-476b-90e6-0d694dd1bff4" />


El atacante asume el rol de un "servidor" falso con una IP de actualización 10.24.20.18. El switch objetivo, operando en modo Server o Client, está programado para aceptar cualquier actualización que provenga de su mismo dominio siempre que el número de revisión sea mayor al que tiene almacenado en su NVRAM. Tras la ejecución del ataque, la base de datos de VLANs del switch (archivo vlan.dat) se sincroniza con la del atacante, eliminando VLANs críticas y creando nuevas etiquetas como la VLAN 999 (HACKED_BY_LUFFY).

<img width="625" height="239" alt="Screenshot 2026-02-27 132551" src="https://github.com/user-attachments/assets/7d33db0f-9eb5-4afe-aba7-da7aa5bd738a" />

---

## III-) Parámetros Técnicos y Manipulación de TLVs

El script utiliza una estructura precisa de paquetes de Capa 2, encapsulados en tramas Ethernet con destino a la dirección multicast de Cisco 01:00:0c:cc:cc:cc y usando encabezados LLC/SNAP. Un aspecto crítico de este script es el manejo de los campos TLV (Type-Length-Value) para definir las propiedades de cada VLAN inyectada (ID, nombre, tipo y MTU). El script maneja una alineación estricta de 80 bytes para el paquete Summary, necesaria para superar las validaciones de ciertas implementaciones de Cisco IOU.

<img width="683" height="762" alt="Screenshot 2026-02-27 160543" src="https://github.com/user-attachments/assets/096b99bf-5f7e-4fc7-a4fc-b3b2d94b7871" />


El parámetro más importante es el TARGET_MD5, un hash de 16 bytes que debe coincidir exactamente con el cálculo que el switch realiza sobre la nueva base de datos; sin este hash correcto, el switch descartará la actualización por error de firma.

<img width="676" height="213" alt="Screenshot 2026-02-27 160603" src="https://github.com/user-attachments/assets/b7683d8b-307d-4b07-8cbd-c2fa208c8e29" />

---

## IV-) Requisitos para la Ejecución

Para que la herramienta funcione con éxito, el entorno debe cumplir con requisitos específicos de red y software. Es imperativo ejecutar el script con privilegios de root debido a la necesidad de manipular sockets raw a través de la librería Scapy. El host atacante debe tener conectividad directa a un puerto troncal, ya que VTP solo se propaga a través de enlaces Trunk. Además, se requiere el conocimiento previo del nombre del dominio VTP y, en caso de que exista una contraseña configurada, el hash MD5 resultante de la combinación de la base de datos y dicho secreto. El script está optimizado para Python 3 y requiere módulos estándar de manejo de estructuras binarias como struct

<img width="407" height="103" alt="Screenshot 2026-02-27 160714" src="https://github.com/user-attachments/assets/a6e7f530-0e4e-4e64-bd36-37b62d22f8bc" />

---

## V-) Medidas de Mitigación y Buenas Prácticas

La defensa contra este tipo de ataques es sencilla pero crítica para la seguridad de la infraestructura. La medida de mitigación principal consiste en desactivar la capacidad de negociación en todos los puertos que no sean troncales legítimos mediante el comando switchport nonegotiate. Asimismo, es fundamental definir explícitamente el modo de cada puerto como acceso con switchport mode access para evitar que el switch intente adivinar el rol del dispositivo conectado. Complementariamente, se recomienda deshabilitar los puertos que no estén en uso y cambiar la VLAN Nativa a una ID que no se utilice en la red, lo cual añade una capa de protección contra el etiquetado doble en caso de una mala configuración del troncal.

Para garantizar que la topología sea resiliente ante ataques de interceptación y denegación de servicio, se ha implementado un esquema de seguridad multicapa que mitiga las vulnerabilidades específicas de los protocolos de infraestructura:

● Seguridad de Capa 2 (DTP, VTP y STP): Se eliminó el riesgo de VLAN Hopping y suplantación de enlaces mediante el uso de switchport nonegotiate y la configuración estática de puertos. La base de datos de VLANs se protegió configurando VTP en modo Transparent con contraseña, lo que ignora actualizaciones externas malintencionadas. Para el protocolo STP, se activó BPDU Guard en los puertos de acceso, asegurando que cualquier switch no autorizado que intente conectarse sea bloqueado inmediatamente, evitando que tome el rol de Root Bridge.

● Protección de Tráfico y MitM (ARP, DHCP y CDP): Se habilitó DHCP Snooping para definir puertos confiables y evitar servidores DHCP falsos. Vinculado a esto, se implementó Dynamic ARP Inspection (DAI) para validar las tramas ARP contra la base de datos de DHCP, neutralizando ataques de ARP Poisoning. Adicionalmente, se desactivó CDP en los puertos que dan hacia el área de usuario para evitar la fuga de información sensible (versión de IOS, IPs de gestión) y se aplicó Port Security para limitar el acceso a una sola MAC por puerto.

● Seguridad de Servicios (DNS y RADIUS): La integridad de la resolución de nombres se protegió mediante ACLs que solo permiten respuestas provenientes del servidor DNS legítimo, bloqueando intentos de Spoofing. Finalmente, el acceso administrativo se centralizó mediante AAA/RADIUS, delegando la autenticación a políticas de red basadas en grupos de Active Directory, lo que garantiza que solo usuarios autorizados en el servidor NPS puedan gestionar los dispositivos de red.

A continuación imágenes de ejemplo (Todas las configuraciones de todo lo que se pidió se puede presenciar en el video).

<img width="364" height="600" alt="Screenshot 2026-02-27 161057" src="https://github.com/user-attachments/assets/1aa49375-ee32-46ed-a205-b40058eaf4d4" />

<img width="519" height="423" alt="Screenshot 2026-02-27 161206" src="https://github.com/user-attachments/assets/00572d6f-47e7-41d0-9ade-b01d45084a69" />

<img width="338" height="101" alt="Screenshot 2026-02-27 161231" src="https://github.com/user-attachments/assets/d58cd1f6-ffb5-4c87-85df-7786f44dc69d" />



