import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  role?: 'STUDENT' | 'INSTRUCTOR';
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/auth';

  private readonly accessTokenKey =
    'skillsphere_access_token';

  private readonly refreshTokenKey =
    'skillsphere_refresh_token';

  private readonly currentUserKey =
    'skillsphere_current_user';


  login(
    data: LoginRequest
  ): Observable<LoginResponse> {

    return this.http
      .post<LoginResponse>(
        `${this.apiUrl}/token/`,
        data
      )
      .pipe(
        tap(response => {

          localStorage.setItem(
            this.accessTokenKey,
            response.access
          );

          localStorage.setItem(
            this.refreshTokenKey,
            response.refresh
          );

        })
      );
  }


  register(
    data: RegisterRequest
  ): Observable<User> {

    return this.http.post<User>(
      `${this.apiUrl}/register/`,
      data
    );
  }


  getCurrentUser(): Observable<User> {

    return this.http
      .get<User>(
        `${this.apiUrl}/me/`
      )
      .pipe(
        tap(user => {

          localStorage.setItem(
            this.currentUserKey,
            JSON.stringify(user)
          );

        })
      );
  }


  getCurrentUserSnapshot(): User | null {

    const storedUser =
      localStorage.getItem(
        this.currentUserKey
      );

    if (!storedUser) {
      return null;
    }

    try {

      return JSON.parse(
        storedUser
      ) as User;

    } catch {

      localStorage.removeItem(
        this.currentUserKey
      );

      return null;
    }
  }


  getAccessToken(): string | null {

    return localStorage.getItem(
      this.accessTokenKey
    );
  }


  getRefreshToken(): string | null {

    return localStorage.getItem(
      this.refreshTokenKey
    );
  }


  isLoggedIn(): boolean {

    return !!this.getAccessToken();
  }


  logout(): void {

    localStorage.removeItem(
      this.accessTokenKey
    );

    localStorage.removeItem(
      this.refreshTokenKey
    );

    localStorage.removeItem(
      this.currentUserKey
    );
  }
} 