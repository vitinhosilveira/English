[app]
title = Ingles do Dia
package.name = inglesdia
package.domain = org.exemplo
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 2.1

# Deixando o ambiente do GitHub escolher as versões compatíveis
requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

# NDK estável, que já vem pré-instalado no Docker do Kivy
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True
