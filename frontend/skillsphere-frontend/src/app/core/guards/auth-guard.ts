import { inject } from '@angular/core';

import {
  CanActivateFn,
  Router
} from '@angular/router';

import { AuthService } from '../services/auth.service';


export const authGuard: CanActivateFn = () => {

  const authService = inject(AuthService);

  const router = inject(Router);

  if (authService.isLoggedIn()) {

    return true;

  }

  return router.createUrlTree(['/login']);

};


export const roleGuard = (
  allowedRoles: string[]
): CanActivateFn => {

  return () => {

    const authService = inject(AuthService);

    const router = inject(Router);

    if (!authService.isLoggedIn()) {

      return router.createUrlTree(['/login']);

    }

    const currentUser =
      authService.getCurrentUserSnapshot();

    if (
      currentUser &&
      allowedRoles.includes(currentUser.role)
    ) {

      return true;

    }

    if (currentUser?.role === 'INSTRUCTOR') {
      return router.createUrlTree(['/instructor/dashboard']);
    }

    return router.createUrlTree(['/dashboard']);
  };

}; 