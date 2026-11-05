import os, json, time, random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

# ---------- TTS NATIVO (jnius) ----------
TTS_READY = False
tts_engine = None

def init_tts():
    global TTS_READY, tts_engine
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
        activity = PythonActivity.mActivity

        class TTSListener(PythonJavaClass):
            __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']
            __javacontext__ = 'app'

            def __init__(self):
                super().__init__()

            @java_method('(I)V')
            def onInit(self, status):
                global TTS_READY
                if status == 0:  # SUCCESS
                    TTS_READY = True

        listener = TTSListener()
        tts_engine = TextToSpeech(activity, listener)
    except Exception as e:
        print("TTS init error:", e)

def falar(txt):
    global tts_engine, TTS_READY
    if tts_engine is None or not TTS_READY:
        return
    try:
        from jnius import autoclass
        Locale = autoclass('java.util.Locale')
        TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
        tts_engine.setLanguage(Locale.US)
        tts_engine.speak(txt, TextToSpeech.QUEUE_FLUSH, None)
    except Exception as e:
        print("TTS speak error:", e)

# ---------- DADOS (Com Dicas de Erro) ----------
# formato: (Inglês, Português, Frase de Exemplo, Dica se errar)
DADOS_NIVEL_1 = [
    ("Hello, how are you?", "Olá, como você está?", "Hello, how are you today?", "Saudação básica. Use 'how are you' para perguntar como a pessoa está."),
    ("My name is...", "Meu nome é...", "My name is Carlos.", "Para se apresentar, use 'My name is' ou apenas 'I am'."),
    ("Nice to meet you", "Prazer em conhecer", "Nice to meet you, Ana.", "Expressão fixa para conhecer alguém. Não traduza ao pé da letra."),
    ("I am from Brazil", "Sou do Brasil", "I am from Brazil.", "Use 'I am from' + país. A preposição é 'from'."),
    ("I don't understand", "Eu não entendo", "Sorry, I don't understand.", "Atenção ao auxiliar negativo: 'don't'."),
    ("Could you repeat?", "Pode repetir?", "Could you repeat, please?", "'Could you' é mais educado que 'Can you'."),
    ("Thank you very much", "Muito obrigado", "Thank you very much for your help.", "Muito obrigado é 'Thank you very much'. Nunca diga 'I thank you'."),
    ("See you tomorrow", "Até amanhã", "See you tomorrow at work.", "'See you' é a forma comum de se despedir."),
]

DADOS_NIVEL_2 = [
    ("I have experience with", "Tenho experiência com", "I have experience with customer service.", "A preposição correta é 'with', não 'in'."),
    ("I am available to start", "Estou disponível para começar", "I am available to start next Monday.", "Use 'available to' + verbo (start)."),
    ("Could you clarify that?", "Pode esclarecer?", "Could you clarify that, please?", "'Clarify' é o verbo para pedir esclarecimento."),
    ("I will send the report", "Vou enviar o relatório", "I will send the report by Friday.", "Use 'send' para enviar. 'Deliver' seria entregar."),
    ("Let's schedule a meeting", "Vamos agendar uma reunião", "Let's schedule a meeting for tomorrow.", "Agendar é 'schedule'. 'Meet' é encontrar."),
    ("My shift starts at", "Meu turno começa às", "My shift starts at 8 a.m.", "Turno de trabalho é 'shift'. Não confunda com 'turn'."),
    ("I need a day off", "Preciso de um dia de folga", "I need a day off next week.", "Folga é 'day off'. Não traduza 'folga' como 'rest'."),
    ("I will follow up", "Vou dar seguimento", "I will follow up on this task.", "Dar seguimento a um assunto é 'follow up'."),
]

DADOS_NIVEL_3 = [
    ("How much is the rent?", "Quanto é o aluguel?", "How much is the rent per month?", "Aluguel é 'rent'. 'Rent' também é o verbo alugar."),
    ("Is it furnished?", "É mobiliado?", "Is the apartment furnished?", "'Furnished' vem de furniture (móveis). Não é 'mobile'."),
    ("I need to fix the sink", "Preciso consertar a pia", "I need to fix the kitchen sink.", "Consertar é 'fix' ou 'repair'. Pia é 'sink'."),
    ("Can I pay by card?", "Posso pagar com cartão?", "Can I pay by card here?", "A preposição é 'by' card. Não é 'with' card."),
    ("I need a receipt", "Preciso de um recibo", "I need a receipt, please.", "Recibo é 'receipt'. Cuidado com a pronúncia (a letra 'p' é silenciosa)."),
]

DADOS_NIVEL_4 = [
    ("I need to see a doctor", "Preciso ver um médico", "I need to see a doctor today.", "Médico é 'doctor'. Não use 'medic' para a profissão."),
    ("I have a headache", "Estou com dor de cabeça", "I have a headache since morning.", "Em inglês, usa-se o artigo: 'I have a headache'."),
    ("Where is the pharmacy?", "Onde é a farmácia?", "Where is the nearest pharmacy?", "Farmácia é 'pharmacy' ou 'drugstore'."),
    ("I want to open an account", "Quero abrir uma conta", "I want to open a checking account.", "Conta corrente é 'checking account' (EUA) ou 'current account' (UK)."),
    ("My card was declined", "Meu cartão foi recusado", "My card was declined at the store.", "Recusado é 'declined'. Não é 'refused' no contexto de cartão."),
]

TODOS_MODULOS = [
    ("Básico 1 - Fundamentos", DADOS_NIVEL_1),
    ("Básico 2 - Trabalho", DADOS_NIVEL_2),
    ("Básico 3 - Moradia e Compras", DADOS_NIVEL_3),
    ("Intermediário - Saúde e Banco", DADOS_NIVEL_4),
]

INTERVALOS = [0, 10, 1440, 4320, 10080, 43200]

def norm(s):
    s = s.lower().strip()
    for a, b in [("á","a"),("à","a"),("â","a"),("ã","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    for ch in ".,!?;:'\"":
        s = s.replace(ch, "")
    return s

class Estado:
    def __init__(self, path):
        self.path = path
        self.data = {"cards":{}, "nivelAtual":0, "historico_erros":[]}
        self.carregar()
    def carregar(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass
    def salvar(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except Exception:
            pass
    def card(self, k):
        c = self.data["cards"].get(k)
        if not c:
            c = {"level":0,"next":0,"ok":0,"err":0}
            self.data["cards"][k] = c
        return c
    def agendar(self, k, acertou):
        c = self.card(k)
        if acertou:
            c["ok"] += 1
            c["level"] = min(5, c["level"] + 1)
        else:
            c["err"] += 1
            c["level"] = max(0, c["level"] - 1)
            self.data["historico_erros"].append(k) # Salva o erro para análise
            if len(self.data["historico_erros"]) > 20:
                self.data["historico_erros"].pop(0)
        c["next"] = int(time.time()*1000) + INTERVALOS[c["level"]]*60000
        self.salvar()
    def pode_abrir(self, idx):
        return idx <= self.data["nivelAtual"]
    def concluido(self, idx):
        return idx < self.data["nivelAtual"]
    def avancar_nivel(self, idx):
        if idx == self.data["nivelAtual"] and idx < len(TODOS_MODULOS) - 1:
            self.data["nivelAtual"] = idx + 1
            self.salvar()

def btn(txt, cb, cor="#4f8cff", h=0.12):
    b = Button(text=txt, size_hint=(1, h), font_size="16sp",
               background_color=get_color_from_hex(cor), background_normal="")
    b.bind(on_release=lambda *_: cb())
    return b

class TelaMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = App.get_running_app()
        self.box = BoxLayout(orientation="vertical", padding=14, spacing=6)
        self.add_widget(self.box)
        self.titulo = Label(text="Inglês do Dia", font_size="26sp", size_hint=(1,0.1),
                            color=get_color_from_hex("#4f8cff"), bold=True)
        self.box.add_widget(self.titulo)
        
        self.scroll = ScrollView(size_hint=(1,0.9))
        self.trilha = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        self.trilha.bind(minimum_height=self.trilha.setter("height"))
        self.scroll.add_widget(self.trilha)
        self.box.add_widget(self.scroll)
        
    def on_pre_enter(self, *a):
        e = self.app.estado
        self.trilha.clear_widgets()
        for i, (nome, _) in enumerate(TODOS_MODULOS):
            bloqueado = not e.pode_abrir(i)
            concluido = e.concluido(i)
            row = BoxLayout(size_hint_y=None, height=70, spacing=6)
            
            status = "ATUAL" if not bloqueado and not concluido else ("CONCLUÍDO" if concluido else "BLOQUEADO")
            cor_status = "#4f8cff" if status == "ATUAL" else ("#22c55e" if status == "CONCLUÍDO" else "#8b93a7")
            
            lbl = Label(text=f"[color={cor_status}]{status}[/color] [b]{nome}[/b]",
                        markup=True, font_size="14sp", halign="left", valign="middle")
            lbl.bind(size=lambda l, *_: setattr(l, "text_size", l.size))
            row.add_widget(lbl)
            
            if bloqueado:
                row.add_widget(Label(text="X", size_hint=(0.2,1), color=get_color_from_hex("#8b93a7")))
            else:
                b = Button(text="Iniciar", size_hint=(0.25,1), font_size="13sp",
                           background_color=get_color_from_hex("#4f8cff"), background_normal="")
                b.bind(on_release=lambda _, idx=i: self.app.iniciar_prova(idx))
                row.add_widget(b)
                
            self.trilha.add_widget(row)

class TelaProva(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = App.get_running_app()
        self.box = BoxLayout(orientation="vertical", padding=14, spacing=8)
        self.add_widget(self.box)
        self.prog = Label(text="", size_hint=(1,0.05), font_size="12sp",
                          color=get_color_from_hex("#8b93a7"))
        self.box.add_widget(self.prog)
        self.conteudo = BoxLayout(orientation="vertical", spacing=8, size_hint=(1,0.95))
        self.box.add_widget(self.conteudo)

    def on_pre_enter(self, *a):
        self.render()

    def render(self):
        s = self.app.sessao
        self.conteudo.clear_widgets()
        
        if s["pos"] >= len(s["ids"]):
            self.fim(); return
            
        self.prog.text = f"Questão {s['pos']+1} de {len(s['ids'])}"
        
        k = s["ids"][s.pos]
        mIdx, iIdx = map(int, k.split("_"))
        item = TODOS_MODULOS[mIdx][1][iIdx]
        en, pt, frase, dica = item
        
        # Escolhe aleatoriamente o modo: Traduzir ou Escrever
        modo = s["modo"]
        
        if modo == "leitura":
            self.conteudo.add_widget(Label(text="Qual é a tradução correta?", font_size="14sp", 
                                           color=get_color_from_hex("#8b93a7")))
            self.conteudo.add_widget(Label(text=en, font_size="22sp", size_hint=(1,0.2),
                                           color=get_color_from_hex("#e6e8ee"), bold=True))
            
            # Gera opções
            pool = [x[1] for x in TODOS_MODULOS[mIdx][1] if x[1] != pt]
            outros = random.sample(pool, min(3, len(pool)))
            opc = [pt] + outros
            random.shuffle(opc)
            
            self.fb = Label(text="", size_hint=(1,0.15), font_size="13sp")
            
            for o in opc:
                b = Button(text=o, size_hint=(1,0.1), font_size="14sp",
                           background_color=get_color_from_hex("#1f232c"), background_normal="")
                b.bind(on_release=lambda inst, val=o: self.responder(val, pt, dica, k))
                self.conteudo.add_widget(b)
                
            self.conteudo.add_widget(self.fb)
            
        elif modo == "escrita":
            self.conteudo.add_widget(Label(text="Traduza para o inglês:", font_size="14sp", 
                                           color=get_color_from_hex("#8b93a7")))
            self.conteudo.add_widget(Label(text=pt, font_size="22sp", size_hint=(1,0.2),
                                           color=get_color_from_hex("#e6e8ee"), bold=True))
            
            self.inp = TextInput(multiline=False, size_hint=(1,0.12), font_size="16sp",
                                 background_color=get_color_from_hex("#1f232c"),
                                 foreground_color=get_color_from_hex("#e6e8ee"))
            self.conteudo.add_widget(self.inp)
            self.fb = Label(text="", size_hint=(1,0.15), font_size="13sp")
            self.conteudo.add_widget(btn("Verificar Resposta", lambda: self.verificar_escrita(en, dica, k)))
            self.conteudo.add_widget(self.fb)

    def responder(self, escolha, correta, dica, k):
        opts = self.conteudo.children[1:5] # Pega os botões de opção
        for o in opts: o.disabled = True
        
        if escolha == correta:
            self.fb.text = "✅ Correto!"
            self.fb.color = get_color_from_hex("#22c55e")
            self.app.estado.agendar(k, True)
            self.app.sessao["ok"] += 1
        else:
            self.fb.text = f"❌ Errado. O correto é: {correta}\n💡 Dica: {dica}"
            self.fb.color = get_color_from_hex("#ef4444")
            self.app.estado.agendar(k, False)
            self.app.sessao["err"] += 1
            
        self.avancar_btn()

    def verificar_escrita(self, en, dica, k):
        ok = norm(self.inp.text) == norm(en)
        if ok:
            self.fb.text = "✅ Correto!"
            self.fb.color = get_color_from_hex("#22c55e")
            self.app.estado.agendar(k, True)
            self.app.sessao["ok"] += 1
        else:
            self.fb.text = f"❌ Errado. O correto é: {en}\n💡 Dica: {dica}"
            self.fb.color = get_color_from_hex("#ef4444")
            self.app.estado.agendar(k, False)
            self.app.sessao["err"] += 1
            
        self.inp.disabled = True
        self.avancar_btn()

    def avancar_btn(self):
        b = btn("Próxima Questão", self.avancar, "#1f232c", 0.1)
        b.color = get_color_from_hex("#ffffff")
        self.conteudo.add_widget(b)

    def avancar(self):
        self.app.sessao["pos"] += 1
        self.app.sessao["modo"] = random.choice(["leitura", "escrita"]) # Muda o modo na próxima
        self.render()

    def fim(self):
        s = self.app.sessao
        total = s["ok"] + s["err"]
        pct = round(s["ok"]/total*100) if total else 100
        
        if pct >= 70:
            self.app.estado.avancar_nivel(s["mod"])
            
        self.conteudo.clear_widgets()
        cor = "#22c55e" if pct >= 70 else "#ef4444"
        
        self.conteudo.add_widget(Label(text=f"{pct}%", font_size="56sp", size_hint=(1,0.4),
                                       color=get_color_from_hex(cor), bold=True))
        self.conteudo.add_widget(Label(text=f"{s['ok']} acertos - {s['err']} erros",
                                       size_hint=(1,0.1), color=get_color_from_hex("#8b93a7")))
                                       
        msg = "Nível concluído! Próximo liberado." if pct >= 70 else "Estude mais! Você precisa de 70%."
        self.conteudo.add_widget(Label(text=msg, size_hint=(1,0.1),
                                       color=get_color_from_hex("#e6e8ee"), font_size="14sp"))
                                       
        self.conteudo.add_widget(btn("Voltar ao menu",
                                     lambda: setattr(self.manager, "current", "menu")))

class InglesApp(App):
    def build(self):
        self.title = "Inglês do Dia"
        base = self.user_data_dir if hasattr(self, "user_data_dir") else "."
        self.estado = Estado(os.path.join(base, "progresso.json"))
        self.sessao = {"mod":0, "pos":0, "ok":0, "err":0, "ids":[], "modo":"leitura"}
        
        sm = ScreenManager()
        sm.add_widget(TelaMenu(name="menu"))
        sm.add_widget(TelaProva(name="prova"))
        return sm
        
    def on_start(self):
        Clock.schedule_once(lambda dt: init_tts(), 0.5)
        
    def iniciar_prova(self, modIdx):
        # Pega todos os itens do nível selecionado
        itens_nivel = TODOS_MODULOS[modIdx][1]
        keys = [f"{modIdx}_{i}" for i in range(len(itens_nivel))]
        
        # Embaralha as questões
        random.shuffle(keys)
        
        self.sessao = {
            "mod": modIdx, "pos": 0, "ok": 0, "err": 0, 
            "ids": keys[:6], # Prova de 6 questões
            "modo": random.choice(["leitura", "escrita"])
        }
        self.root.current = "prova"

if __name__ == "__main__":
    InglesApp().run()
