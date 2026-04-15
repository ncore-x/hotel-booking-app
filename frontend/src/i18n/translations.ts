export const translations = {
  en: {
    // Header / Nav
    nav: {
      home: "Home",
      destinations: "Destinations",
      admin: "Admin",
      myBookings: "My Bookings",
      myProfile: "My Account",
      signOut: "Sign Out",
      logIn: "Log In",
      signUp: "Sign Up",
    },

    // SearchBar
    search: {
      location: "Location",
      locationPlaceholder: "Where are you going?",
      hotelName: "Hotel Name",
      hotelNamePlaceholder: "Grand Hotel…",
      checkIn: "Check In",
      checkOut: "Check Out",
      nights: (n: number) => `${n} ${n === 1 ? "night" : "nights"}`,
      searchButton: "Search",
      destination: "Destination",
      destinationPlaceholder: "City, hotel or area",
      sections: {
        regions: "Regions",
        hotels: "Hotels",
      },
      guests: "Guests",
      guestsLabel: (n: number) => `${n} ${n === 1 ? "guest" : "guests"}`,
      adults: "Adults",
      done: "Done",
    },

    // HomePage
    home: {
      heroTitle: "Find Your\nDream Getaway",
      heroSubtitle: "Discover handpicked hotels across the globe — from hidden retreats to city icons.",
      exploreLocations: "Explore by Location",
      allLocations: "All",
      trendingTitle: "Top Trending Hotels",
      popularDestinations: "Popular Destinations",
      viewHotels: "View hotels",
      browseAll: "Browse all",
      testimonialsTitle: "What Our Guests Say",
      footerCta: {
        title: "Ready to Find Your Perfect Stay?",
        subtitle: "Thousands of properties. One seamless experience.",
        button: "View Available Dates",
      },
      testimonials: [
        {
          name: "Sofia K.",
          city: "Berlin, Germany",
          text: "Booked in under two minutes. The room was exactly as pictured — spotless, quiet, and the breakfast was outstanding.",
          rating: 5,
        },
        {
          name: "Marco T.",
          city: "Milan, Italy",
          text: "StaySpring recommended a hotel I'd never have found on my own. Genuinely surprised by the quality for the price.",
          rating: 5,
        },
        {
          name: "Priya N.",
          city: "Mumbai, India",
          text: "The filters are a dream. I found a pet-friendly, sea-view suite in fifteen seconds flat. Will use every trip.",
          rating: 5,
        },
        {
          name: "James L.",
          city: "London, UK",
          text: "Cancelled a booking at midnight, refund landed by morning. Customer service that actually works.",
          rating: 5,
        },
      ],
    },

    // HotelDetailPage
    hotelDetail: {
      backToSearch: "Back to Search",
      availableRooms: "Available Rooms",
      noRooms: "No rooms available for the selected dates",
      selectDates: "Select Your Dates",
      checkIn: "Check In",
      checkOut: "Check Out",
      nights: "Nights",
      chooseBelowToBook: "Choose a room below to book",
    },

    // RoomCard
    roomCard: {
      perNight: "/ night",
      book: "Book Now",
      guests: (n: number) => `${n} ${n === 1 ? "guest" : "guests"}`,
      quantity: (n: number) => `${n} ${n === 1 ? "room" : "rooms"} available`,
    },

    // BookingSummary
    bookingSummary: {
      title: "Booking Summary",
      room: "Room",
      checkIn: "Check-in",
      checkOut: "Check-out",
      pricePerNight: "Per night",
      total: "Total",
    },

    // LoginPage
    login: {
      title: "Welcome Back",
      subtitle: "Sign in to manage your bookings and profile.",
      email: "Email",
      password: "Password",
      submit: "Sign In",
      noAccount: "Don't have an account?",
      signUp: "Sign up",
      error: "Invalid email or password.",
      orContinueWith: "Or continue with",
      oauthError: "OAuth sign-in failed. Please try again.",
      oauthConflict: "This email is already registered via a different sign-in method.",
      oauthNotConfigured: "This sign-in method is not available.",
    },

    // RegisterPage
    register: {
      title: "Create Account",
      subtitle: "Join thousands of travellers finding their perfect stay.",
      email: "Email",
      password: "Password",
      confirmPassword: "Confirm Password",
      submit: "Create Account",
      hasAccount: "Already have an account?",
      logIn: "Log in",
      passwordMismatch: "Passwords do not match.",
      passwordTooShort: "Password must be at least 6 characters.",
      orContinueWith: "Or continue with",
    },

    // OAuthCallbackPage
    oauthCallback: {
      loading: "Signing you in…",
      error: "Sign-in failed. Please try again.",
      conflict: "This email is already registered via a different sign-in method.",
    },

    // MyBookingsPage
    myBookings: {
      title: "My Bookings",
      all: "All",
      upcoming: "Upcoming",
      active: "Active",
      completed: "Completed",
      empty: "No bookings found.",
      emptySubtitle: "Your confirmed stays will appear here.",
      browseHotels: "Browse Hotels",
    },

    // ProfilePage
    profilePage: {
      title: "My Profile",
      profileSettings: "Profile Settings",
      profileSubtitle: "Fill in your details to autofill booking forms.",
      firstName: "First Name",
      lastName: "Last Name",
      birthDate: "Date of Birth",
      citizenship: "Citizenship",
      gender: "Gender",
      genderMale: "Male",
      genderFemale: "Female",
      phone: "Phone",
      emailReadonly: "Email",
      emailReadonlyHint: "Email cannot be changed here",
      profileSuccess: "Profile saved.",
      profileError: "Failed to save profile.",
      changePassword: "Change Password",
      changeEmail: "Change Email",
      currentPassword: "Current Password",
      newPassword: "New Password",
      confirmPassword: "Confirm New Password",
      passwordMismatch: "Passwords do not match.",
      newEmail: "New Email",
      save: "Save Changes",
      success: "Updated successfully.",
      passwordSent: "Confirmation link sent to your email. Follow the link to apply the change.",
      passwordSuccess: "Password updated successfully.",
      passwordError: "Failed to update password.",
      emailSent: (email: string) => `Confirmation link sent to ${email}. Follow the link to apply the change.`,
      emailSuccess: "Email updated successfully.",
      emailError: "Failed to update email.",
      confirmSuccess: "Change confirmed successfully.",
      confirmError: "The link is invalid or has already been used.",
      confirmLoading: "Applying change…",
      linkedAccounts: "Sign-in Methods",
      linkedAccountsSubtitle: "Accounts you can use to sign in.",
      passwordMethod: "Password",
      passwordMethodDesc: "Sign in with email and password",
      googleMethod: "Google",
      googleMethodDesc: "Sign in with your Google account",
      githubMethod: "GitHub",
      githubMethodDesc: "Sign in with your GitHub account",
      connected: "Connected",
      notConnected: "Not connected",
    },

    // BookingCard
    bookingCard: {
      checkIn: "Check-in",
      checkOut: "Check-out",
      nights: (n: number) => `${n} ${n === 1 ? "night" : "nights"}`,
      perNightLabel: "/ night",
      totalLabel: "Total",
      status: {
        upcoming: "Upcoming",
        active: "Active now",
        completed: "Completed",
      },
      edit: "Edit Dates",
      cancel: "Cancel",
    },

    // BookingConfirmPage
    bookingConfirm: {
      backToHotel: "Back to hotel",
      title: "Confirm Booking",
      cancel: "Cancel",
      confirm: "Confirm Booking",
      booked: "Booked!",
      loadError: "Failed to load booking data",
      createError: "Failed to create booking",
    },

    // Notifications panel
    notifications: {
      title: "Notifications",
      markAllRead: "Mark all read",
      clearAll: "Clear all",
      empty: "No notifications yet.",
      bookingCreatedTitle: "Booking confirmed",
      bookingCreatedBody: (id: number, hotelTitle: string, city: string) =>
        `Booking #${id} at ${hotelTitle}, ${city}`,
      bookingCancelledTitle: "Booking cancelled",
      bookingCancelledBody: (id: number) => `Booking #${id} has been cancelled.`,
      bookingUpdatedTitle: "Dates rescheduled",
      bookingUpdatedBody: (id: number, dateFrom: string, dateTo: string) =>
        `Booking #${id}: ${dateFrom} → ${dateTo}`,
      passwordSentTitle: "Password change requested",
      passwordSentBody: "Follow the link in your inbox to confirm.",
      emailSentTitle: "Email change requested",
      emailSentBody: (email: string) => `Confirmation link sent to ${email}.`,
    },

    // Common
    common: {
      loading: "Loading…",
      error: "Something went wrong. Please try again.",
      notFound: "Not found.",
      perNight: "/ night",
      from: "from",
      stars: (n: number) => `${n} stars`,
    },

    // Footer
    footer: {
      tagline: "Find your perfect stay, anywhere in the world.",
      menu: "Menu",
      links: {
        home: "Home",
        destinations: "Destinations",
        hotels: "Hotels",
        about: "About",
      },
      social: "Social",
      privacy: "Company",
      privacyLinks: {
        privacy: "Privacy Policy",
        terms: "Terms of Use",
        cookies: "Cookie Policy",
      },
      copyright: (year: number) => `© ${year} StaySpring. All rights reserved.`,
    },
  },

  ru: {
    nav: {
      home: "Главная",
      destinations: "Направления",
      admin: "Админ",
      myBookings: "Мои бронирования",
      myProfile: "Личный кабинет",
      signOut: "Выйти",
      logIn: "Войти",
      signUp: "Регистрация",
    },

    search: {
      location: "Город",
      locationPlaceholder: "Куда едете?",
      hotelName: "Название отеля",
      hotelNamePlaceholder: "Grand Hotel…",
      checkIn: "Заезд",
      checkOut: "Выезд",
      searchButton: "Найти",
      nights: (n: number) => {
        const mod = n % 10;
        const mod100 = n % 100;
        if (mod === 1 && mod100 !== 11) return `${n} ночь`;
        if (mod >= 2 && mod <= 4 && (mod100 < 10 || mod100 >= 20)) return `${n} ночи`;
        return `${n} ночей`;
      },
      destination: "Направление",
      destinationPlaceholder: "Город, отель или район",
      sections: {
        regions: "Регионы",
        hotels: "Отели",
      },
      guests: "Гости",
      guestsLabel: (n: number) => {
        const mod = n % 10;
        const mod100 = n % 100;
        let word: string;
        if (mod === 1 && mod100 !== 11) word = "гость";
        else if (mod >= 2 && mod <= 4 && (mod100 < 10 || mod100 >= 20)) word = "гостя";
        else word = "гостей";
        return `${n} ${word}`;
      },
      adults: "Взрослые",
      done: "Готово",
    },

    home: {
      heroTitle: "Найдите отдых\nмечты",
      heroSubtitle: "Тщательно отобранные отели по всему миру — от уютных бутиков до культовых городских адресов.",
      exploreLocations: "Популярные направления",
      allLocations: "Все",
      trendingTitle: "Популярные отели",
      popularDestinations: "Популярные направления",
      viewHotels: "Смотреть отели",
      browseAll: "Смотреть все",
      testimonialsTitle: "Что говорят гости",
      footerCta: {
        title: "Готовы найти идеальный отель?",
        subtitle: "Тысячи объектов. Один удобный сервис.",
        button: "Посмотреть свободные даты",
      },
      testimonials: [
        {
          name: "Sophia K.",
          city: "Берлин, Германия",
          text: "Забронировала за две минуты. Номер в точности как на фото — чистый, тихий, а завтрак превзошёл ожидания.",
          rating: 5,
        },
        {
          name: "Marco T.",
          city: "Милан, Италия",
          text: "StaySpring порекомендовал отель, который я бы сам никогда не нашёл. Качество за эти деньги — настоящий сюрприз.",
          rating: 5,
        },
        {
          name: "Priya N.",
          city: "Мумбаи, Индия",
          text: "Фильтры — мечта. Нашла номер с видом на море, куда можно с питомцем, за пятнадцать секунд. Теперь только так.",
          rating: 5,
        },
        {
          name: "James L.",
          city: "Лондон, Великобритания",
          text: "Отменил бронь в полночь — деньги вернулись к утру. Это и есть настоящий сервис.",
          rating: 5,
        },
      ],
    },

    hotelDetail: {
      backToSearch: "Назад к поиску",
      availableRooms: "Доступные номера",
      noRooms: "На выбранные даты нет свободных номеров",
      selectDates: "Выберите даты",
      checkIn: "Заезд",
      checkOut: "Выезд",
      nights: "Ночей",
      chooseBelowToBook: "Выберите номер ниже для бронирования",
    },

    roomCard: {
      perNight: "/ ночь",
      book: "Забронировать",
      guests: (n: number) => {
        const mod = n % 10;
        const mod100 = n % 100;
        if (mod === 1 && mod100 !== 11) return `${n} гость`;
        if (mod >= 2 && mod <= 4 && (mod100 < 10 || mod100 >= 20)) return `${n} гостя`;
        return `${n} гостей`;
      },
      quantity: (n: number) => {
        const mod = n % 10;
        const mod100 = n % 100;
        if (mod === 1 && mod100 !== 11) return `${n} номер доступен`;
        if (mod >= 2 && mod <= 4 && (mod100 < 10 || mod100 >= 20)) return `${n} номера доступно`;
        return `${n} номеров доступно`;
      },
    },

    bookingSummary: {
      title: "Детали бронирования",
      room: "Номер",
      checkIn: "Заезд",
      checkOut: "Выезд",
      pricePerNight: "Цена за ночь",
      total: "Итого",
    },

    login: {
      title: "С возвращением",
      subtitle: "Войдите, чтобы управлять бронированиями и профилем.",
      email: "Email",
      password: "Пароль",
      submit: "Войти",
      noAccount: "Нет аккаунта?",
      signUp: "Зарегистрироваться",
      error: "Неверный email или пароль.",
      orContinueWith: "Или войдите через",
      oauthError: "Ошибка OAuth. Попробуйте снова.",
      oauthConflict: "Этот email уже зарегистрирован через другой способ входа.",
      oauthNotConfigured: "Этот способ входа недоступен.",
    },

    register: {
      title: "Создать аккаунт",
      subtitle: "Присоединяйтесь к тысячам путешественников.",
      email: "Email",
      password: "Пароль",
      confirmPassword: "Подтвердите пароль",
      submit: "Создать аккаунт",
      hasAccount: "Уже есть аккаунт?",
      logIn: "Войти",
      passwordMismatch: "Пароли не совпадают.",
      passwordTooShort: "Пароль должен содержать не менее 6 символов.",
      orContinueWith: "Или зарегистрируйтесь через",
    },

    oauthCallback: {
      loading: "Выполняем вход…",
      error: "Ошибка входа. Попробуйте снова.",
      conflict: "Этот email уже зарегистрирован через другой способ входа.",
    },

    myBookings: {
      title: "Мои бронирования",
      all: "Все",
      upcoming: "Предстоящие",
      active: "Сейчас",
      completed: "Завершённые",
      empty: "Бронирований не найдено.",
      emptySubtitle: "Здесь появятся ваши подтверждённые поездки.",
      browseHotels: "Найти отели",
    },

    profilePage: {
      title: "Мой профиль",
      profileSettings: "Настройки профиля",
      profileSubtitle: "Укажите свои данные, чтобы при бронировании они заполнялись автоматически.",
      firstName: "Имя",
      lastName: "Фамилия",
      birthDate: "Дата рождения",
      citizenship: "Гражданство",
      gender: "Пол",
      genderMale: "Мужчина",
      genderFemale: "Женщина",
      phone: "Телефон",
      emailReadonly: "Электронная почта",
      emailReadonlyHint: "Email изменяется в разделе ниже",
      profileSuccess: "Профиль сохранён.",
      profileError: "Не удалось сохранить профиль.",
      changePassword: "Изменить пароль",
      changeEmail: "Изменить email",
      currentPassword: "Текущий пароль",
      newPassword: "Новый пароль",
      confirmPassword: "Подтвердите новый пароль",
      passwordMismatch: "Пароли не совпадают.",
      newEmail: "Новый email",
      save: "Сохранить",
      success: "Успешно обновлено.",
      passwordSent: "Письмо с подтверждением отправлено на вашу почту. Перейдите по ссылке для применения изменений.",
      passwordSuccess: "Пароль успешно изменён.",
      passwordError: "Не удалось изменить пароль.",
      emailSent: (email: string) => `Письмо с подтверждением отправлено на ${email}. Перейдите по ссылке для применения изменений.`,
      emailSuccess: "Email успешно изменён.",
      emailError: "Не удалось изменить email.",
      confirmSuccess: "Изменение успешно подтверждено.",
      confirmError: "Ссылка недействительна или уже использована.",
      confirmLoading: "Применяем изменение…",
      linkedAccounts: "Способы входа",
      linkedAccountsSubtitle: "Аккаунты, через которые можно войти в систему.",
      passwordMethod: "Пароль",
      passwordMethodDesc: "Вход по email и паролю",
      googleMethod: "Google",
      googleMethodDesc: "Вход через аккаунт Google",
      githubMethod: "GitHub",
      githubMethodDesc: "Вход через аккаунт GitHub",
      connected: "Подключён",
      notConnected: "Не подключён",
    },

    bookingCard: {
      checkIn: "Заезд",
      checkOut: "Выезд",
      nights: (n: number) => {
        const mod = n % 10;
        const mod100 = n % 100;
        if (mod === 1 && mod100 !== 11) return `${n} ночь`;
        if (mod >= 2 && mod <= 4 && (mod100 < 10 || mod100 >= 20)) return `${n} ночи`;
        return `${n} ночей`;
      },
      perNightLabel: "/ ночь",
      totalLabel: "Итого",
      status: {
        upcoming: "Предстоит",
        active: "Сейчас",
        completed: "Завершено",
      },
      edit: "Изменить даты",
      cancel: "Отменить",
    },

    bookingConfirm: {
      backToHotel: "Назад к отелю",
      title: "Подтверждение бронирования",
      cancel: "Отмена",
      confirm: "Подтвердить бронирование",
      booked: "Забронировано!",
      loadError: "Не удалось загрузить данные",
      createError: "Не удалось создать бронирование",
    },

    notifications: {
      title: "Уведомления",
      markAllRead: "Прочитать все",
      clearAll: "Очистить",
      empty: "Пока нет уведомлений.",
      bookingCreatedTitle: "Бронирование создано",
      bookingCreatedBody: (id: number, hotelTitle: string, city: string) =>
        `Бронирование #${id} в ${hotelTitle}, ${city}`,
      bookingCancelledTitle: "Бронирование отменено",
      bookingCancelledBody: (id: number) => `Бронирование #${id} отменено.`,
      bookingUpdatedTitle: "Даты перенесены",
      bookingUpdatedBody: (id: number, dateFrom: string, dateTo: string) =>
        `Бронирование #${id}: ${dateFrom} → ${dateTo}`,
      passwordSentTitle: "Запрос на смену пароля",
      passwordSentBody: "Перейдите по ссылке в письме для подтверждения.",
      emailSentTitle: "Запрос на смену email",
      emailSentBody: (email: string) => `Ссылка подтверждения отправлена на ${email}.`,
    },

    common: {
      loading: "Загрузка…",
      error: "Что-то пошло не так. Попробуйте снова.",
      notFound: "Не найдено.",
      perNight: "/ ночь",
      from: "от",
      stars: (n: number) => `${n} звезды`,
    },

    footer: {
      tagline: "Найдите идеальный отель в любой точке мира.",
      menu: "Меню",
      links: {
        home: "Главная",
        destinations: "Направления",
        hotels: "Отели",
        about: "О нас",
      },
      social: "Соцсети",
      privacy: "Компания",
      privacyLinks: {
        privacy: "Политика конфиденциальности",
        terms: "Условия использования",
        cookies: "Cookie-политика",
      },
      copyright: (year: number) => `© ${year} StaySpring. Все права защищены.`,
    },
  },
} as const;

export type Translations = typeof translations.en;
