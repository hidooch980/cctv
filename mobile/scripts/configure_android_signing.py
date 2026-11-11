from pathlib import Path
import sys

app = Path(sys.argv[1])
gradle = next((p for p in (app / "build.gradle.kts", app / "build.gradle") if p.exists()), None)
if gradle is None:
    raise SystemExit("Android app Gradle file not found")
text = gradle.read_text()
if "signingConfigs" in text and "release" in text:
    print(f"Release signing configuration already present in {gradle.name}")
    raise SystemExit(0)

if gradle.suffix == ".kts":
    prefix = '''
import java.util.Properties

val signingProps = Properties()
val signingPropsFile = rootProject.file("key.properties")
if (signingPropsFile.exists()) {
    signingPropsFile.inputStream().use { signingProps.load(it) }
}

'''
    text = prefix + text
    marker = "    buildTypes {"
    config = '''    signingConfigs {
        create("release") {
            keyAlias = signingProps["keyAlias"] as String?
            keyPassword = signingProps["keyPassword"] as String?
            storeFile = (signingProps["storeFile"] as String?)?.let { file(it) }
            storePassword = signingProps["storePassword"] as String?
        }
    }

'''
    if marker not in text:
        raise SystemExit("Could not locate Android buildTypes block")
    text = text.replace(marker, config + marker, 1)
    text = text.replace('''            signingConfig = signingConfigs.getByName("debug")''',
                        '''            signingConfig = signingConfigs.getByName("release")''', 1)
    if 'signingConfig = signingConfigs.getByName("release")' not in text:
        # Flutter templates can omit an explicit debug signing line.
        text = text.replace('''        getByName("release") {''',
                            '''        getByName("release") {
            signingConfig = signingConfigs.getByName("release")''', 1)
else:
    prefix = '''
def signingProps = new Properties()
def signingPropsFile = rootProject.file("key.properties")
if (signingPropsFile.exists()) {
    signingPropsFile.withInputStream { signingProps.load(it) }
}

'''
    text = prefix + text
    marker = "    buildTypes {"
    config = '''    signingConfigs {
        release {
            keyAlias signingProps['keyAlias']
            keyPassword signingProps['keyPassword']
            storeFile signingProps['storeFile'] ? file(signingProps['storeFile']) : null
            storePassword signingProps['storePassword']
        }
    }

'''
    if marker not in text:
        raise SystemExit("Could not locate Android buildTypes block")
    text = text.replace(marker, config + marker, 1)
    text = text.replace("signingConfig signingConfigs.debug", "signingConfig signingConfigs.release", 1)
    if "signingConfig signingConfigs.release" not in text:
        text = text.replace("release {", "release {\n            signingConfig signingConfigs.release", 1)

gradle.write_text(text)
print(f"Configured release signing in {gradle}")
