[app]
title = Ingles do Dia
package.name = inglesdia
package.domain = org.exemplo
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 2.1

# AQUI ESTÁ O SEGREDO: Versões fixas e sem plyer problemático
requirements = python3==3.11.9,kivy==2.3.0,pyjnius==1.6.1

orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True
