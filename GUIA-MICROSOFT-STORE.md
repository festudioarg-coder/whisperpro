# Guía: publicar WhisperPRO en la Microsoft Store
> Verificado al 12/10/2026 con la documentación oficial de Microsoft (fuentes al final). Lo marcado ⚠️ no se pudo confirmar.

## La idea en una línea
Cuenta gratis de desarrollador → reservar el nombre → yo armo un paquete **MSIX** (Microsoft lo firma gratis, sin aviso de "app desconocida") → vos lo subís con la ficha, la política de privacidad y las notas para el revisor → aprobación en hasta 3 días hábiles.

El instalador actual (Inno .exe) **no sirve para la Store** sin un certificado pago: la vía EXE/MSI exige firmar el instalador y todos los .exe/.dll con un certificado de una autoridad reconocida, y alojarlo en un servidor propio. Con MSIX no hace falta nada de eso.

---

## PASO 0 — Decisión antes de registrarte: ¿cuenta Individual o Empresa?
- **Individual:** gratis, verificación con DNI y selfie, se habilita en minutos. Microsoft la define como cuenta para quien publica "sin relación con su negocio o profesión". **No se puede convertir a Empresa después.**
- **Empresa (Company):** requiere una entidad legal registrada (SRL, SAS…). Hace falta para cobrar con tus propios medios de pago dentro de la app (política 10.8.3).
- ⚠️ No está claro si un monotributista califica como Empresa. **Antes de elegir, consultá a soporte de Microsoft:** aka.ms/windowsdevelopersupport (preguntá: "Soy monotributista en Argentina y quiero publicar una app gratis que más adelante tendrá planes pagos con cobro propio: ¿cuenta Individual o Company?").
- Mi sugerencia: si FESTUDIOS no es sociedad todavía, publicar la versión **gratis** con cuenta Individual y abrir la de Empresa cuando haya planes pagos.

## PASO 1 — Registrarte (vos, desde el navegador, ~15 min)
1. Entrá a **https://storedeveloper.microsoft.com** → **"Get started for free"**. Tiene que ser por ahí: si entrás por Partner Center directo o por Visual Studio te puede aparecer el registro viejo, que es pago.
2. Elegí el tipo de cuenta (Paso 0) e iniciá sesión con una cuenta Microsoft. Conviene una cuenta dedicada a FESTUDIOS.
3. Verificación de identidad: foto del DNI o pasaporte y una selfie, desde el celular, con buena luz.
4. **País: Argentina** (no se puede cambiar después). ⚠️ No encontré una lista oficial que nombre a Argentina, pero el programa dice que funciona en casi 200 mercados.
5. Revisá los datos y tocá **"Go to Partner Center dashboard"**. Si no aparece **Apps & Games**, esperá unos 5 minutos y recargá, o entrá a https://aka.ms/submitwindowsapp.

## PASO 2 — Reservar el nombre y pasarme 3 datos (vos, 5 min)
1. **Apps & Games → New product → MSIX or PWA app** → reservá el nombre.
   - Se reserva por 3 meses.
   - Si todavía no elegimos el nombre definitivo, se puede reservar más de uno.
   - ⚠️ El nombre "WhisperPRO" contiene "Whisper", que es un modelo de OpenAI: posible problema de marca.
2. Andá a **Product management → Product identity** y copiame exactamente estos 3 datos:
   - `Package/Identity/Name`
   - `Package/Identity/Publisher` (empieza con `CN=`)
   - `PublisherDisplayName`

   No son secretos: es tu identidad pública en la Store.

## PASO 3 — Lo preparo yo (archivos)
1. **Cambios en la app para funcionar empaquetada:**
   - La app detecta que corre desde la Store.
   - El inicio con Windows pasa a hacerlo la Store (*startupTask*) en vez del acceso directo actual.
   - Los datos se guardan donde la Store permite.
   - Si falta WebView2, la app avisa en lugar de romperse.
   - Si se niega el permiso de micrófono, la app lo explica.
2. **Archivo de descripción del paquete (`AppxManifest.xml`)** con tus 3 datos y lo que declara:
   - Permisos: micrófono, internet y *runFullTrust*. Este último lo usan las apps de escritorio clásicas y hay que justificarlo.
   - Versión con formato `1.0.0.0`.
3. **Logos** en todos los tamaños que pide la Store (50, 44, 150, 300 px y variantes), sacados del logo actual.
4. **`build_store.bat`:** genera el `.msix` con `makeappx`, que viene en el Windows SDK.
5. **Prueba local:**
   - Instalar el paquete en tu PC en modo desarrollador.
   - Probar: Win+Espacio, escribir en el Bloc de notas y en Chrome, bandeja, inicio con Windows, historial.
   - Pasar el Windows App Certification Kit (WACK), la prueba oficial de Microsoft.
6. **Borradores de texto:**
   - Política de privacidad.
   - Descripción de la ficha.
   - Notas para el revisor.
   - Justificación de *runFullTrust*.

## PASO 4 — Publicar la política de privacidad (vos)
- Es obligatoria para apps de escritorio.
- Una página pública, por ejemplo **festudios.pro/whisperpro/privacidad**. Yo te paso el texto y vos la subís como hacés siempre.
- Tiene que decir:
  - que la app usa el micrófono;
  - que el audio va directo de la PC del usuario a Groq, con la clave del usuario;
  - que FESTUDIOS no recibe ni guarda nada;
  - que el historial queda solo en la PC;
  - que el atajo de teclado global solo detecta Win+Espacio y no guarda ni envía lo que se tipea.

## PASO 5 — Enviar a revisión (vos en Partner Center, con mis textos)
1. **Packages:** subir el `.msix` sin firmar (Microsoft lo firma).
2. **Properties:**
   - Categoría: Productividad.
   - URL de la política de privacidad.
   - Soporte: tu mail.
3. **Age ratings:** cuestionario IARC, 5 minutos.
4. **Store listing:**
   - Descripción.
   - Mínimo 1 captura de 1366×768 o mayor (mejor 4).
   - Ícono de 300×300.
   - El nombre no puede tener palabras de marketing.
5. **Pricing:** Gratis.
6. **Submission options → Notes for certification:** acá está el riesgo principal.
   - **El revisor necesita probar la app y sin clave de Groq no anda.** Le damos una clave de prueba creada solo para eso y la borramos después de aprobada.
   - Explicamos el atajo global en lenguaje claro, para que no lo confundan con un registrador de teclas.
7. **Restricted capabilities:** justificar *runFullTrust*.
8. Enviar. La certificación tarda **hasta 3 días hábiles** (un caso real: unas 48 h la primera vez y menos de 24 h las actualizaciones). Una vez aprobada, aparece en la Store en unos 15 minutos.

## PASO 6 — Después
- **Actualizaciones:** se sube un `.msix` con versión mayor y la Store se lo instala sola a todos.
- **Cobrar más adelante:** en apps que no son juegos se puede usar Mercado Pago o Stripe y **Microsoft se queda con el 0%**. Con el sistema de cobro de Microsoft, la comisión es del 15%. Para cobrar con medios propios hace falta cuenta de Empresa (ver Paso 0).
- **winget (canal extra, gratis):** al estar en la Store, ya se puede instalar con `winget install --source msstore`.

## Riesgos y cómo los cubrimos
| Riesgo | Cómo lo cubrimos |
|---|---|
| El revisor ve el atajo global como "keylogger" | Notas claras para el revisor, la política de privacidad lo explica y el código no guarda teclas |
| El revisor no puede probar la app | Clave de prueba temporal en las notas |
| Los datos en %APPDATA% quedan "virtualizados" y se borran al desinstalar | Aceptado: es lo normal en la Store; el historial se puede exportar |
| El antivirus da un falso positivo por el empaquetado de Python (PyInstaller) | Si pasa, se recompila el bootloader o se reporta como falso positivo |
| Tipo de cuenta equivocado | Consultar a soporte antes (Paso 0) |
| ⚠️ El atajo y la escritura en otras apps no andan dentro del paquete | Muy probable que sí anden, pero lo probamos localmente antes de enviar |

## Fuentes
- [Registro gratis para individuos (Windows Blog, 2025)](https://blogs.windows.com/windowsdeveloper/2025/09/10/free-developer-registration-for-individual-developers-on-microsoft-store/)
- [Abrir cuenta de desarrollador](https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/open-a-developer-account)
- [Elegir vía de distribución](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/choose-distribution-path)
- [Requisitos MSIX](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements)
- [Requisitos EXE/MSI](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/app-package-requirements)
- [Proceso de certificación](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-certification-process)
- [Capturas e imágenes](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/screenshots-and-images)
- [Políticas de la Store](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies)
- [SmartScreen y la Store](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
- [FAQ: comisiones](https://learn.microsoft.com/en-us/windows/apps/publish/faq/get-started-with-the-microsoft-store)
- [Virtualización de AppData en MSIX](https://learn.microsoft.com/en-us/windows/msix/desktop/flexible-virtualization)
- [StartupTask](https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-desktop-startuptasks)
- [Permisos de apps (capabilities)](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/app-capability-declarations)
