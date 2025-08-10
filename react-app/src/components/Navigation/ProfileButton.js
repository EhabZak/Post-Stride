import React, { useState, useEffect, useRef } from "react";
import { useDispatch } from "react-redux";
import { logout } from "../../store/session";
import OpenModalButton from "../OpenModalButton";
import LoginFormModal from "../LoginFormModal";
import SignupFormModal from "../SignupFormModal";
import "./Navigation.css";

function ProfileButton({ user }) {
  const dispatch = useDispatch();
  const [showMenu, setShowMenu] = useState(false);
  const ulRef = useRef();
  const wrapperRef = useRef();

  const openMenu = () => {
    if (showMenu) return;
    setShowMenu(true);
  };

  const closeMenu = () => setShowMenu(false);

  const handleMouseEnter = () => {
    setShowMenu(true);
  };

  const handleMouseLeave = () => {
    setShowMenu(false);
  };

  useEffect(() => {
    if (!showMenu) return;

    const closeMenuOnClick = (e) => {
      if (!ulRef.current.contains(e.target)) {
        setShowMenu(false);
      }
    };

    document.addEventListener("click", closeMenuOnClick);

    return () => document.removeEventListener("click", closeMenuOnClick);
  }, [showMenu]);

  const handleLogout = (e) => {
    e.preventDefault();
    dispatch(logout());
  };

  const ulClassName = "profile-dropdown" + (showMenu ? "" : " hidden");

  return (
    <>
    <div 
      className="profile-menu-wrapper" 
      ref={wrapperRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button onClick={openMenu}>
        {/* <i className="fas fa-user-circle" /> */}
        <h1 className='tezi'>Get Started</h1>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <circle cx="8"  cy="8"  r="2.5"/>
    <circle cx="16" cy="8"  r="2.5"/>
    <circle cx="8"  cy="16" r="2.5"/>
    <circle cx="16" cy="16" r="2.5"/>
  </svg>
        
      </button>
      <ul className={ulClassName} ref={ulRef}>
        {user ? (
          <>
            <li>{user.username}</li>
            <li>{user.email}</li>
            <li>
              <button onClick={handleLogout}>Log Out</button>
            </li>
          </>
        ) : (
          <>
            <OpenModalButton
              buttonText="Log In"
              onItemClick={closeMenu}
              modalComponent={<LoginFormModal />}
              className="LogIn"
            />

            <OpenModalButton
              buttonText="Free Trial"
              onItemClick={closeMenu}
              modalComponent={<SignupFormModal />}
              className="getStarted"
            />
          </>
          
        )}
       
      </ul>
      </div>
    </>
  );
}

export default ProfileButton;
