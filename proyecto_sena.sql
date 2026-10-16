drop database if exists ebanisteria;
create database ebanisteria;
use ebanisteria;
create table acudientes (
    id_acudiente int primary key,
    nombre varchar(100),
    correo varchar(100),
    telefono varchar(10),
    tipo_acudiente varchar(20)
);

create table usuarios (
    id_usuario int auto_increment primary key,
    documento varchar(30),
	NombreCompleto varchar(100),
	grado varchar(15) default "0000",
    email varchar(255),
    contraseña varchar(255) not null,
    rol varchar(20) default "estudiante" not null,
    estado varchar(10) default 'activo'
);


insert into usuarios values(1,"10255424511","Andres","0000","admin@gmail.com","12","admin","activo");
insert into usuarios values(2,"102554241","Estudiante","0000","est@prueba","12","estudiante","activo");
insert into usuarios values(3,"102554241a","Estudiante","0000","est@pruedba","12","estudiante","activo");
create table herramientas (
    id_herramienta int primary key auto_increment,
    nombre varchar(100) not null,
    estado varchar(10),
    cantidad int,
    tipo varchar(100),
    descripcion text,
    fecha_prestamo date,
    activo tinyint(1) not null default 1
);
 

create table estudiantes_acudientes (
    id_estudiantefk int,
    id_acudientefk int,
    primary key(id_estudiantefk, id_acudientefk),
    foreign key (id_estudiantefk) references usuarios(id_usuario),
    foreign key (id_acudientefk) references acudientes(id_acudiente)
);

create table prestamos (
    id_prestamo int auto_increment primary key,
    id_estudiantefk int,
    id_acudientefk int,
    id_docentefk int,
    id_herramientafk int,
    fecha_entrega date,
    fecha_devolucion date,
    estado_solicitud varchar(20) not null default 'Aprobado',
    foreign key (id_estudiantefk) references usuarios(id_usuario),
    foreign key (id_acudientefk) references acudientes(id_acudiente),
    foreign key (id_docentefk) references usuarios(id_usuario),
    foreign key (id_herramientafk) references herramientas(id_herramienta)
);


-- Registro de los reportes PDF generados (se crea también automáticamente al iniciar la app)
create table reportes (
    id_reporte int auto_increment primary key,
    fecha_generacion datetime not null default current_timestamp,
    fecha_desde date not null,
    fecha_hasta date not null,
    id_adminfk int null,
    total_solicitudes int not null default 0,
    total_aprobadas int not null default 0,
    total_devueltas int not null default 0,
    total_rechazadas int not null default 0,
    total_pendientes int not null default 0,
    foreign key (id_adminfk) references usuarios(id_usuario)
);

select * from herramientas;

delimiter //
 
create procedure listar_herramientas()
begin
    select id_herramienta, nombre, tipo, cantidad, estado, descripcion
    from herramientas
    where activo = 1;
end //
 
delimiter ;
 
call listar_herramientas();
 
delimiter //
 
create procedure buscar_herramientas(in p_id int)
begin
    select id_herramienta, nombre, tipo, cantidad, estado, descripcion
    from herramientas
    where id_herramienta = p_id
    and activo = 1;
end //
 
delimiter ;
 
call buscar_herramientas(1);
 
delimiter //
 
create procedure insertar_herramienta(
    in p_nombre varchar(100),
    in p_estado varchar(10),
    in p_cantidad int,
    in p_tipo varchar(100),
    in p_descripcion text
)
begin
    insert into herramientas (
        nombre,
        estado,
        cantidad,
        tipo,
        descripcion,
        activo
    )
    values (
        p_nombre,
        p_estado,
        p_cantidad,
        p_tipo,
        p_descripcion,
        1
    );
end //
 
delimiter ;

delimiter //
create procedure registrarusuario(
	in p_documento varchar(30),
	in p_NombreCompleto varchar(100),
	in p_grado varchar (15),
    in p_email varchar(200),
    in p_contraseña varchar(255)
)
begin 
	insert into usuarios(documento,NombreCompleto,grado,email,contraseña) values (p_documento,p_NombreCompleto,p_grado,p_email,p_contraseña);
end //

delimiter ;
select * from usuarios;
