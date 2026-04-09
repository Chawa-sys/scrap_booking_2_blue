const passwordIcon = document.querySelectorAll('.password__icon')
const authPassword = document.querySelectorAll('.auth__password')

// Mostrar/Ocultar contraseña
for (let i = 0; i < passwordIcon.length; ++i) {
    passwordIcon[i].addEventListener('click', (e) => {
        const lastArray = e.target.classList.length - 1
        if (e.target.classList[lastArray] === 'bi-eye-slash') {
            e.target.classList.remove('bi-eye-slash')
            e.target.classList.add('bi-eye')
            e.currentTarget.parentNode.querySelector('input').type = 'text'
        } else {
            e.target.classList.add('bi-eye-slash')
            e.target.classList.remove('bi-eye')
            e.currentTarget.parentNode.querySelector('input').type = 'password'
        }
    });
};
