from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            user.update_last_login()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            
            flash('Вы успешно вошли в систему', 'success')
            return redirect(next_page)
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('auth/register.html')
        
        # Проверка существования пользователя
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
            return render_template('auth/register.html')
        
        # Создание пользователя
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            is_admin=False  # Первый пользователь не админ
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация прошла успешно. Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth.route('/profile')
@login_required
def profile():
    """Профиль пользователя"""
    return render_template('auth/profile.html')

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Изменение пароля"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Текущий пароль неверен', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('Новые пароли не совпадают', 'error')
            return render_template('auth/change_password.html')
        
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Пароль успешно изменен', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')
