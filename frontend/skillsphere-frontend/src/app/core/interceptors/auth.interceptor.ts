import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router, { optional: true });
  const accessToken = localStorage.getItem(
    'skillsphere_access_token'
  );

  const authReq = accessToken
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${accessToken}`
        }
      })
    : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !req.url.includes('/auth/token/')) {
        localStorage.removeItem('skillsphere_access_token');
        localStorage.removeItem('skillsphere_refresh_token');
        localStorage.removeItem('skillsphere_current_user');
        if (router) {
          router.navigate(['/login']);
        }
      }
      return throwError(() => error);
    })
  );
};