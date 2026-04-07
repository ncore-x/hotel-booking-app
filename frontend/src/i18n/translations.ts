export const translations = {
  en: {
    // Header / Nav
    nav: {
      home: "Home",
      destinations: "Destinations",
      admin: "Admin",
      myBookings: "My Bookings",
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
      changePassword: "Change Password",
      changeEmail: "Change Email",
      currentPassword: "Current Password",
      newPassword: "New Password",
      newEmail: "New Email",
      save: "Save Changes",
      success: "Updated successfully.",
      passwordSuccess: "Password updated successfully.",
      passwordError: "Failed to update password.",
      emailSuccess: "Email updated successfully.",
      emailError: "Failed to update email.",
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
      changePassword: "Изменить пароль",
      changeEmail: "Изменить email",
      currentPassword: "Текущий пароль",
      newPassword: "Новый пароль",
      newEmail: "Новый email",
      save: "Сохранить",
      success: "Успешно обновлено.",
      passwordSuccess: "Пароль успешно изменён.",
      passwordError: "Не удалось изменить пароль.",
      emailSuccess: "Email успешно изменён.",
      emailError: "Не удалось изменить email.",
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
