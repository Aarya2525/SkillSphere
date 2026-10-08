import {
  HttpContextToken,
  HttpErrorResponse,
  HttpInterceptorFn
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const IS_RETRY_REQUEST = new HttpContextToken<boolean>(() => false);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService, { optional: true });
  const router = inject(Router, { optional: true });

  const isAuthEndpoint =
    req.url.includes('/auth/token/') ||
    req.url.includes('/auth/register/');
  const isRetry = req.context.get(IS_RETRY_REQUEST);

  const accessToken =
    authService?.getAccessToken() ??
    localStorage.getItem('skillsphere_access_token');

  const authReq = accessToken && !req.headers.has('Authorization')
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${accessToken}`
        }
      })
    : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !isAuthEndpoint && !isRetry) {
        const refreshToken =
          authService?.getRefreshToken() ??
          localStorage.getItem('skillsphere_refresh_token');

        if (refreshToken && authService) {
          return authService.refreshToken().pipe(
            switchMap(tokenResponse => {
              const retriedReq = req.clone({
                setHeaders: {
                  Authorization: `Bearer ${tokenResponse.access}`
                },
                context: req.context.set(IS_RETRY_REQUEST, true)
              });
              return next(retriedReq);
            }),
            catchError(refreshError => {
              authService.logout();
              if (router) {
                router.navigate(['/login']);
              }
              return throwError(() => refreshError);
            })
          );
        }

        // Missing refresh token: clear stale session and navigate to login
        if (authService) {
          authService.logout();
        } else {
          localStorage.removeItem('skillsphere_access_token');
          localStorage.removeItem('skillsphere_refresh_token');
          localStorage.removeItem('skillsphere_current_user');
        }
        if (router) {
          router.navigate(['/login']);
        }
      } else if (error.status === 401 && isRetry) {
        // Failed even after refreshing: clear and navigate to login (prevent loop)
        if (authService) {
          authService.logout();
        } else {
          localStorage.removeItem('skillsphere_access_token');
          localStorage.removeItem('skillsphere_refresh_token');
          localStorage.removeItem('skillsphere_current_user');
        }
        if (router) {
          router.navigate(['/login']);
        }
      }

      return throwError(() => error);
    })
  );
};