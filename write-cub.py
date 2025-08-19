import os
import json
import zlib
import base64
import struct
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

class CubitsTextProcessor:
    def __init__(self):
        self.current_file = None
        self.text_content = ""
        self.metadata = {}
        
    def generate_cubits_matrix(self, byte_val):
        """Genera la matriz CUBITs 6x8 para un byte dado"""
        binary_byte = bin(byte_val)[2:].zfill(8)
        matrix = []
        
        for i in range(6):
            row = []
            for j in range(8):
                target_pos = (j + i) % 8
                row.append(binary_byte[target_pos])
            matrix.append(''.join(row))
            
        return matrix
    
    def optimize_cubits_sequence(self, matrix):
        """Optimiza la secuencia CUBITs concatenando bits hasta obtener valores imprimibles"""
        optimized_bytes = bytearray()
        bit_accumulator = ""
        
        for row in matrix:
            # Convertir la fila a valor decimal
            row_value = int(row, 2)
            
            # Si el valor es imprimible (32-126), añadirlo directamente
            if 32 <= row_value <= 126:
                optimized_bytes.append(row_value)
            else:
                # Acumular bits para formar valores más grandes
                bit_accumulator += row
                
                # Cuando tengamos suficientes bits, procesarlos
                while len(bit_accumulator) >= 8:
                    byte_bits = bit_accumulator[:8]
                    byte_val = int(byte_bits, 2)
                    
                    # Solo añadir si es imprimible
                    if 32 <= byte_val <= 126:
                        optimized_bytes.append(byte_val)
                    else:
                        # Si no es imprimible, usar codificación especial
                        optimized_bytes.extend(self.encode_special_value(byte_val))
                    
                    bit_accumulator = bit_accumulator[8:]
        
        # Procesar bits restantes
        if bit_accumulator:
            # Rellenar con ceros y codificar
            padded_bits = bit_accumulator.ljust(8, '0')
            byte_val = int(padded_bits, 2)
            if 32 <= byte_val <= 126:
                optimized_bytes.append(byte_val)
            else:
                optimized_bytes.extend(self.encode_special_value(byte_val))
        
        return bytes(optimized_bytes)
    
    def encode_special_value(self, byte_val):
        """Codifica valores no imprimibles en una secuencia especial"""
        # Usar un prefijo especial y luego el valor en base64
        return f"\\x{byte_val:02x}".encode('utf-8')
    
    def decode_special_value(self, encoded_seq):
        """Decodifica valores de la secuencia especial"""
        if encoded_seq.startswith(b'\\x'):
            try:
                return int(encoded_seq[2:4], 16)
            except:
                return 0
        return 0
    
    def encode_to_cubits(self, text, metadata=None):
        """Codifica texto a formato CUBITs optimizado"""
        if metadata is None:
            metadata = {
                "encoding": "UTF-8-CUBITs",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "version": "1.0"
            }
        
        # Convertir metadatos a bytes
        metadata_bytes = json.dumps(metadata).encode('utf-8')
        
        # Codificar texto con optimización CUBITs
        encoded_data = bytearray()
        for char in text:
            byte_val = ord(char)
            matrix = self.generate_cubits_matrix(byte_val)
            optimized = self.optimize_cubits_sequence(matrix)
            encoded_data.extend(optimized)
        
        # Combinar metadatos y contenido
        combined = (len(metadata_bytes)).to_bytes(4, 'big') + metadata_bytes + encoded_data
        
        # Comprimir el resultado
        compressed = zlib.compress(combined)
        
        return base64.b64encode(compressed).decode('ascii')
    
    def decode_from_cubits(self, cubits_data):
        """Decodifica datos CUBITs optimizados"""
        try:
            # Decodificar base64 y descomprimir
            decoded = base64.b64decode(cubits_data)
            decompressed = zlib.decompress(decoded)
            
            # Extraer metadatos
            meta_length = int.from_bytes(decompressed[:4], 'big')
            metadata = json.loads(decompressed[4:4+meta_length].decode('utf-8'))
            
            # Decodificar contenido
            content_data = decompressed[4+meta_length:]
            decoded_text = self.decode_cubits_content(content_data)
            
            return decoded_text, metadata
            
        except Exception as e:
            return f"Error decodificando: {str(e)}", {}
    
    def decode_cubits_content(self, content_data):
        """Decodifica el contenido CUBITs optimizado"""
        decoded_text = ""
        i = 0
        
        while i < len(content_data):
            # Intentar decodificar el siguiente carácter
            if content_data[i] == ord('\\') and i + 3 < len(content_data) and content_data[i+1] == ord('x'):
                # Es una secuencia especial
                special_val = self.decode_special_value(content_data[i:i+4])
                decoded_text += chr(special_val)
                i += 4
            else:
                # Carácter normal
                decoded_text += chr(content_data[i])
                i += 1
        
        return decoded_text
    
    def save_document(self, filename, text, metadata=None):
        """Guarda un documento en formato .cub"""
        cubits_data = self.encode_to_cubits(text, metadata)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(cubits_data)
        
        return True
    
    def load_document(self, filename):
        """Carga un documento .cub"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                cubits_data = f.read()
            
            text, metadata = self.decode_from_cubits(cubits_data)
            return text, metadata, True
        except Exception as e:
            return f"Error: {str(e)}", {}, False

class CubitsTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesador de Texto CUBITs")
        self.root.geometry("800x600")
        
        self.processor = CubitsTextProcessor()
        self.current_file = None
        self.text_content = ""
        self.metadata = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Barra de menú
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Nuevo", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Abrir", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Guardar", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Guardar como", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.exit_app)
        
        # Menú Editar
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Metadatos", command=self.edit_metadata)
        edit_menu.add_command(label="Estadísticas", command=self.show_stats)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        
        # Área de texto
        ttk.Label(main_frame, text="Editor de Texto CUBITs").grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        self.text_area = tk.Text(main_frame, wrap=tk.WORD, undo=True)
        self.text_area.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Barra de desplazamiento
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.text_area.config(yscrollcommand=scrollbar.set)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Atajos de teclado
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
    
    def new_file(self):
        if self.check_save():
            self.text_area.delete(1.0, tk.END)
            self.current_file = None
            self.metadata = {
                "title": "Documento sin título",
                "author": "",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "version": "1.0"
            }
            self.update_title()
            self.status_var.set("Nuevo documento creado")
    
    def open_file(self):
        if self.check_save():
            filename = filedialog.askopenfilename(
                title="Abrir documento CUBITs",
                filetypes=[("Documentos CUBITs", "*.cub"), ("Todos los archivos", "*.*")]
            )
            
            if filename:
                try:
                    text, metadata, success = self.processor.load_document(filename)
                    if success:
                        self.text_area.delete(1.0, tk.END)
                        self.text_area.insert(1.0, text)
                        self.current_file = filename
                        self.metadata = metadata
                        self.update_title()
                        self.status_var.set(f"Documento cargado: {filename}")
                    else:
                        messagebox.showerror("Error", f"No se pudo cargar el documento: {text}")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar el documento: {str(e)}")
    
    def save_file(self):
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()
    
    def save_as_file(self):
        filename = filedialog.asksaveasfilename(
            title="Guardar documento CUBITs",
            defaultextension=".cub",
            filetypes=[("Documentos CUBITs", "*.cub"), ("Todos los archivos", "*.*")]
        )
        
        if filename:
            self.save_to_file(filename)
    
    def save_to_file(self, filename):
        try:
            text = self.text_area.get(1.0, tk.END)
            self.metadata["modified"] = datetime.now().isoformat()
            
            success = self.processor.save_document(filename, text, self.metadata)
            if success:
                self.current_file = filename
                self.update_title()
                self.status_var.set(f"Documento guardado: {filename}")
            else:
                messagebox.showerror("Error", "No se pudo guardar el documento")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
    
    def edit_metadata(self):
        # Crear ventana de edición de metadatos
        meta_win = tk.Toplevel(self.root)
        meta_win.title("Metadatos del Documento")
        meta_win.geometry("400x300")
        
        # Frame principal
        main_frame = ttk.Frame(meta_win, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        meta_win.columnconfigure(0, weight=1)
        meta_win.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Campos de metadatos
        ttk.Label(main_frame, text="Título:").grid(row=0, column=0, sticky=tk.W, pady=2)
        title_var = tk.StringVar(value=self.metadata.get("title", ""))
        ttk.Entry(main_frame, textvariable=title_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(main_frame, text="Autor:").grid(row=1, column=0, sticky=tk.W, pady=2)
        author_var = tk.StringVar(value=self.metadata.get("author", ""))
        ttk.Entry(main_frame, textvariable=author_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(main_frame, text="Descripción:").grid(row=2, column=0, sticky=tk.W, pady=2)
        desc_var = tk.StringVar(value=self.metadata.get("description", ""))
        ttk.Entry(main_frame, textvariable=desc_var).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(main_frame, text="Etiquetas (separadas por comas):").grid(row=3, column=0, sticky=tk.W, pady=2)
        tags_var = tk.StringVar(value=", ".join(self.metadata.get("tags", [])))
        ttk.Entry(main_frame, textvariable=tags_var).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        def save_metadata():
            self.metadata["title"] = title_var.get()
            self.metadata["author"] = author_var.get()
            self.metadata["description"] = desc_var.get()
            self.metadata["tags"] = [tag.strip() for tag in tags_var.get().split(",") if tag.strip()]
            meta_win.destroy()
            self.status_var.set("Metadatos actualizados")
        
        ttk.Button(btn_frame, text="Guardar", command=save_metadata).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=meta_win.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_stats(self):
        text = self.text_area.get(1.0, tk.END)
        stats = {
            "Caracteres": len(text),
            "Palabras": len(text.split()),
            "Líneas": text.count('\n'),
            "Tamaño original (bytes)": len(text.encode('utf-8')),
            "Metadatos": len(json.dumps(self.metadata).encode('utf-8'))
        }
        
        stats_text = "\n".join([f"{k}: {v}" for k, v in stats.items()])
        messagebox.showinfo("Estadísticas del Documento", stats_text)
    
    def show_about(self):
        about_text = """Procesador de Texto CUBITs v1.0

Sistema avanzado de procesamiento de texto que utiliza la tecnología CUBITs para almacenamiento multidimensional de información.

Características:
- Almacenamiento de metadatos integrados
- Compresión optimizada con transformación CUBITs
- Interfaz intuitiva similar a WordPad
- Formato .cub para documentos enriquecidos

Desarrollado para demostrar el potencial de la tecnología CUBITs en el procesamiento de documentos."""
        messagebox.showinfo("Acerca de", about_text)
    
    def check_save(self):
        text = self.text_area.get(1.0, tk.END)
        if text.strip() and self.current_file is None:
            result = messagebox.askyesnocancel("Guardar", "¿Desea guardar el documento actual?")
            if result is None:  # Cancelar
                return False
            elif result:  # Sí
                self.save_as_file()
        return True
    
    def update_title(self):
        title = "Procesador de Texto CUBITs"
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        self.root.title(title)
    
    def exit_app(self):
        if self.check_save():
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = CubitsTextEditor(root)
    root.mainloop()
