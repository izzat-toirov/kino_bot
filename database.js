const fs = require('fs');
const path = require('path');

const DB_FILE = path.join(__dirname, 'database.json');

class Database {
  constructor() {
    this.data = {
      movies: [],
      users: [],
      channels: []
    };
    this.load();
  }

  load() {
    try {
      if (fs.existsSync(DB_FILE)) {
        const raw = fs.readFileSync(DB_FILE, 'utf8');
        this.data = JSON.parse(raw);
        if (!this.data.movies) this.data.movies = [];
        if (!this.data.users) this.data.users = [];
        if (!this.data.channels) this.data.channels = [];
      } else {
        this.save();
      }
    } catch (err) {
      console.error('Baza faylini o\'qishda xatolik:', err);
    }
  }

  save() {
    try {
      fs.writeFileSync(DB_FILE, JSON.stringify(this.data, null, 2), 'utf8');
    } catch (err) {
      console.error('Baza faylini saqlashda xatolik:', err);
    }
  }

  // ================= FOYDALANUVCHILAR ================= //
  addUser(userId, username, firstName) {
    const id = Number(userId);
    const existing = this.data.users.find((u) => u.user_id === id);
    if (!existing) {
      this.data.users.push({
        user_id: id,
        username: username || '',
        first_name: firstName || '',
        joined_at: new Date().toISOString()
      });
      this.save();
      return true;
    }
    return false;
  }

  getTotalUsersCount() {
    return this.data.users.length;
  }

  getAllUserIds() {
    return this.data.users.map((u) => u.user_id);
  }

  // ================= KINOLAR ================= //
  addMovie(code, title, fileId, description = '') {
    const c = Number(code);
    const index = this.data.movies.findIndex((m) => m.code === c);
    const movieObj = {
      code: c,
      title: title.trim(),
      file_id: fileId,
      description: (description || '').trim(),
      views: index >= 0 ? this.data.movies[index].views : 0,
      created_at: new Date().toISOString()
    };

    if (index >= 0) {
      this.data.movies[index] = movieObj;
    } else {
      this.data.movies.push(movieObj);
    }
    this.save();
    return true;
  }

  movieExists(code) {
    const c = Number(code);
    return this.data.movies.some((m) => m.code === c);
  }

  getMovie(code) {
    const c = Number(code);
    const movie = this.data.movies.find((m) => m.code === c);
    if (movie) {
      movie.views = (movie.views || 0) + 1;
      this.save();
      return movie;
    }
    return null;
  }

  deleteMovie(code) {
    const c = Number(code);
    const initialLen = this.data.movies.length;
    this.data.movies = this.data.movies.filter((m) => m.code !== c);
    if (this.data.movies.length !== initialLen) {
      this.save();
      return true;
    }
    return false;
  }

  searchMovies(query, limit = 10) {
    const q = query.toLowerCase().trim();
    return this.data.movies
      .filter((m) => (m.title && m.title.toLowerCase().includes(q)) || (m.description && m.description.toLowerCase().includes(q)))
      .sort((a, b) => (b.views || 0) - (a.views || 0))
      .slice(0, limit);
  }

  getRandomMovie() {
    if (!this.data.movies.length) return null;
    const randomIndex = Math.floor(Math.random() * this.data.movies.length);
    const movie = this.data.movies[randomIndex];
    movie.views = (movie.views || 0) + 1;
    this.save();
    return movie;
  }

  getLatestMovies(limit = 8) {
    return [...this.data.movies]
      .sort((a, b) => b.code - a.code)
      .slice(0, limit);
  }

  getTopMovies(limit = 5) {
    return [...this.data.movies]
      .sort((a, b) => (b.views || 0) - (a.views || 0))
      .slice(0, limit);
  }

  getTotalMoviesCount() {
    return this.data.movies.length;
  }

  // ================= MAJBURIY OBUNA KANALLARI ================= //
  addChannel(channelId, name, inviteLink) {
    const id = channelId.trim();
    const index = this.data.channels.findIndex((ch) => ch.channel_id === id);
    const channelObj = {
      channel_id: id,
      name: name.trim(),
      invite_link: inviteLink.trim()
    };

    if (index >= 0) {
      this.data.channels[index] = channelObj;
    } else {
      this.data.channels.push(channelObj);
    }
    this.save();
    return true;
  }

  deleteChannel(channelId) {
    const id = channelId.trim();
    const initialLen = this.data.channels.length;
    this.data.channels = this.data.channels.filter((ch) => ch.channel_id !== id);
    if (this.data.channels.length !== initialLen) {
      this.save();
      return true;
    }
    return false;
  }

  getAllChannels() {
    return this.data.channels;
  }
}

module.exports = new Database();
