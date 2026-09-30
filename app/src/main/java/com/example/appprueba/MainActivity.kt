package com.example.appprueba

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val etUsuario = findViewById<EditText>(R.id.etUsuario)
        val etPassword = findViewById<EditText>(R.id.etPassword)
        val btnLogin = findViewById<Button>(R.id.btnLogin)
        val tvMensaje = findViewById<TextView>(R.id.tvMensaje)

        btnLogin.setOnClickListener {
            val user = etUsuario.text.toString().trim()
            val pass = etPassword.text.toString()

            tvMensaje.text = when {
                user.isEmpty() || pass.isEmpty() -> "Complete todos los campos"
                user == "juan" && pass == "1234" -> "Bienvenido, admin"
                else -> "Credenciales incorrectas"
            }
        }
    }
}