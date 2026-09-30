import os
import time
import subprocess
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Variables de entorno y rutas por defecto
APP = os.getenv("APK_PATH", os.path.abspath("apk/app-debug.apk"))
PKG = "com.example.appprueba"
SERVER = os.getenv("APPIUM_SERVER", "http://127.0.0.1:4723")
EMU = os.getenv("EMULATOR_ID", "emulator-5554")

# ---------------------------------------------------------------------------
# Fixture & Configuración (Capabilities + Conexión)
# ---------------------------------------------------------------------------
@pytest.fixture
def driver():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Android Emulator"
    options.app = APP
    options.new_command_timeout = 120
    
    # ⏱️ Timeouts extendidos para evitar 'timed out' en GitHub Actions / CI/CD
    options.set_capability("appium:uiautomator2ServerInstallTimeout", 90000)
    options.set_capability("appium:adbExecTimeout", 90000)
    
    # Soporte para dispositivo físico si se define UDID
    if os.getenv("UDID"):
        options.udid = os.getenv("UDID")
        
    drv = webdriver.Remote(SERVER, options=options)
    yield drv
    drv.quit()

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def adb(*args):
    """Ejecuta comandos de ADB directamente en el emulador por defecto."""
    subprocess.run(["adb", "-s", EMU] + list(args), check=True)

def find(driver, res_id):
    """Busca y espera la presencia de un elemento por su ID dentro del paquete."""
    return WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((AppiumBy.ID, f"{PKG}:id/{res_id}"))
    )

def login(driver, user, password):
    """Realiza la secuencia de inicio de sesión y retorna el texto del mensaje."""
    if user:
        find(driver, "etUsuario").send_keys(user)
    if password:
        find(driver, "etPassword").send_keys(password)
        
    find(driver, "btnLogin").click()
    return find(driver, "tvMensaje").text

def tomar_evidencia(driver, nombre_archivo):
    """Crea la carpeta 'evidencias' y guarda la captura de pantalla."""
    os.makedirs("evidencias", exist_ok=True)
    driver.save_screenshot(f"evidencias/{nombre_archivo}.png")

# ---------------------------------------------------------------------------
# 1. Testing Funcional
# ---------------------------------------------------------------------------
def test_login_valido(driver):
    assert "Bienvenido" in login(driver, "juan", "1234")
    tomar_evidencia(driver, "test_login_valido")

def test_login_invalido(driver):
    assert login(driver, "admin", "0000") == "Credenciales incorrectas"
    tomar_evidencia(driver, "test_login_invalido")

def test_campos_vacios(driver):
    assert login(driver, "", "") == "Complete todos los campos"
    tomar_evidencia(driver, "test_campos_vacios")

def test_password_enmascarada(driver):
    find(driver, "etPassword").send_keys("1234")
    tomar_evidencia(driver, "test_password_enmascarada")
    assert find(driver, "etPassword").get_attribute("password") == "true"

# ---------------------------------------------------------------------------
# 2. Testing de Usabilidad
# ---------------------------------------------------------------------------
def test_boton_tamano_tactil(driver):
    btn = find(driver, "btnLogin")
    tomar_evidencia(driver, "test_boton_tamano_tactil")
    min_px = 48 * driver.get_display_density() / 160
    assert btn.size["height"] >= min_px

# ---------------------------------------------------------------------------
# 3. Testing de Compatibilidad
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("orientacion", ["PORTRAIT", "LANDSCAPE"])
def test_orientacion(driver, orientacion):
    driver.orientation = orientacion
    time.sleep(1)  # Pausa para estabilizar la rotación del layout
    
    # 📸 Toma la captura MIENTRAS la pantalla está rotada
    tomar_evidencia(driver, f"test_orientacion_{orientacion.lower()}")
    
    for r in ("etUsuario", "etPassword", "btnLogin"):
        assert find(driver, r).is_displayed()
        
    driver.orientation = "PORTRAIT"

# ---------------------------------------------------------------------------
# 4. Testing de Interrupciones
# ---------------------------------------------------------------------------
def test_segundo_plano_conserva_texto(driver):
    find(driver, "etUsuario").send_keys("admin")
    driver.execute_script("mobile: backgroundApp", {"seconds": 3})
    
    # 📸 Toma captura inmediatamente al regresar del segundo plano
    tomar_evidencia(driver, "test_segundo_plano_conserva_texto")
    assert find(driver, "etUsuario").text == "admin"

def test_notificaciones(driver):
    driver.open_notifications()
    time.sleep(1)
    
    # 📸 CAPTURA AHORA: Con la barra de notificaciones desplegada sobre la app
    tomar_evidencia(driver, "test_notificaciones")
    
    driver.press_keycode(4)  # KeyCode 4 = Botón Atrás (cierra las notificaciones)
    time.sleep(1)
    assert find(driver, "btnLogin").is_displayed()

def test_llamada_entrante(driver):
    # Genera la llamada simulada en el emulador
    adb("emu", "gsm", "call", "5551234")
    time.sleep(2)
    
    # 📸 CAPTURA AHORA: Con la pantalla/alerta de llamada entrante activa
    tomar_evidencia(driver, "test_llamada_entrante")
    
    adb("emu", "gsm", "cancel", "5551234")
    time.sleep(2)
    driver.activate_app(PKG)
    assert find(driver, "btnLogin").is_displayed()

def test_bateria_baja(driver):
    adb("emu", "power", "capacity", "5")
    time.sleep(1)
    
    # 📸 CAPTURA AHORA: Con el nivel crítico de batería al 5%
    tomar_evidencia(driver, "test_bateria_baja")
    
    try:
        driver.press_keycode(4)  # Descarta diálogos flotantes del sistema si existen
    except Exception:
        pass
        
    assert "Bienvenido" in login(driver, "juan", "1234")
    adb("emu", "power", "capacity", "100")

def test_perdida_de_conexion(driver):
    try:
        driver.execute_script("mobile: setConnectivity", {"wifi": False, "data": False})
        time.sleep(1)
        
        # 📸 CAPTURA AHORA: Con las conexiones deshabilitadas
        tomar_evidencia(driver, "test_perdida_de_conexion")
        
        assert "Bienvenido" in login(driver, "juan", "1234")
    finally:
        # Restablece la conectividad al finalizar
        driver.execute_script("mobile: setConnectivity", {"wifi": True, "data": True})
        time.sleep(1)